import pyGandalf.examples.OpenGL.ProceduralTerrain.D1.Noise as Noise
import numpy as np

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolate on the scale given by a to b, using t as the point on that scale.
    Examples
    --------
        50 == lerp(0, 100, 0.5)
        4.2 == lerp(1, 5, 0.8)
    """
    return (1 - t) * a + t * b

# From: https://gist.github.com/laundmo/b224b1f4c8ef6ca5fe47e132c8deab56
def inv_lerp(a: float, b: float, v: float) -> float:
    """Inverse Linar Interpolation, get the fraction between a and b on which v resides.
    Examples
    --------
        0.5 == inv_lerp(0, 100, 50)
        0.8 == inv_lerp(1, 5, 4.2)
    """
    return (v - a) / (b - a)

class Terrain:
    noiseLayers = []
    minHeight = 0
    maxHeight = 0
    def __init__(self, scale, elevationScale, mapSize, fallOffEnabled, fallOffType, a, b, fallOffHeight,):
        self.scale : float = scale
        self.elevationScale : float = elevationScale
        self.mapSize : int = mapSize
        self.fallOffEnabled : bool = fallOffEnabled
        self.fallOffType : int = fallOffType

        self.a : float = a
        self.b : float = b
        self.fallOffHeight : float = fallOffHeight

    def AddNoiseLayer(self, noiseSettings):
        self.noiseLayers.append(noiseSettings)

    def Start(self):
        self.minTerrainHeight = []
        self.maxTerrainHeight = []
        self.heightMap = [[[0.0 for x in range(0, self.mapSize, 1)] for z in range(0, self.mapSize, 1)] for i in range(0, len(self.noiseLayers), 1)]
        self.heights = [[0.0 for x in range(0, self.mapSize, 1)] for z in range(0, self.mapSize, 1)]
        self.vertices = [[0.0, 0.0, 0.0] for x in range(0, self.mapSize * self.mapSize, 1)]
        self.indices = [0 for x in range(0, (self.mapSize - 1) * (self.mapSize - 1) * 6, 1)]
        for i in range(0, len(self.noiseLayers), 1):
            self.minTerrainHeight.append(100)
            self.maxTerrainHeight.append(0)
        self.minHeight = 100
        self.maxHeight = 0

    def ApplyFallOff(self, x, z, height):
        distFromCenter = 0
        h = 0
        if(self.fallOffType == Noise.typeOfFallOff.Circle):
            distFromCenter = np.power(x - 0.5, 2) + np.power(z - 0.5, 2)
            distFromCenter *= 2
        elif(self.fallOffType == Noise.typeOfFallOff.Rectangle):
            distFromCenter = max(np.abs(x - 1.0), np.abs(z - 1.0))
        h = np.power(distFromCenter, self.a) / (np.power(distFromCenter, self.a) + np.power(self.b - self.b * distFromCenter, self.a))
        if(height > self.fallOffHeight):
            return lerp(height, self.fallOffHeight, h)
        else:
            clampedHeight = height
            #if(not self.underWaterRavines):
             #   clampedHeight = self.fallOffHeight
            return lerp(height, clampedHeight, h)

    def CreateHeightMap(self):
        self.Start()

        for i in range(0, len(self.noiseLayers), 1):
            for z in range(0, self.mapSize, 1):
                for x in range(0, self.mapSize, 1):
                    self.heightMap[i][z][x] = Noise.Noise(x, z, self.noiseLayers[i], self.mapSize)
                    self.minTerrainHeight[i] = min(self.minTerrainHeight[i], self.heightMap[i][z][x])
                    self.maxTerrainHeight[i] = max(self.maxTerrainHeight[i], self.heightMap[i][z][x])

        for z in range(0, self.mapSize, 1):
            zCoord = z / (self.mapSize - 1.0)
            for x in range(0, self.mapSize, 1):   
                xCoord = x / (self.mapSize - 1.0)
                height = 0
                mask = 1
                for l in range(0, len(self.noiseLayers), 1):
                    if self.noiseLayers[l].layerActive:
                        self.heightMap[l][z][x] = inv_lerp(self.minTerrainHeight[l], self.maxTerrainHeight[l], self.heightMap[l][z][x])
                        if l != 0:
                            if (self.noiseLayers[l].useFirstLayerAsMask):
                                mask = self.heightMap[0][z][x]
                            else:
                                mask = 1
                        height += self.heightMap[l][z][x] * mask

                if self.fallOffEnabled:
                    height = self.ApplyFallOff(xCoord, zCoord, height)
                self.minHeight = min(self.minHeight, height)
                self.maxHeight = max(self.maxHeight, height)
                self.heights[z][x] = height
            
        for z in range(0, self.mapSize, 1):
            for x in range(0, self.mapSize, 1):
                self.heights[z][x] = inv_lerp(self.minHeight, self.maxHeight, self.heights[z][x])

        self.Generate()

    def Generate(self):
        v = 0
        t = 0
        i = 0

        for z in range(0, self.mapSize, 1):
            zCoord = (z / (self.mapSize - 1.0)) * 2
            for x in range(0, self.mapSize, 1):
                xCoord = (x / (self.mapSize - 1.0)) * 2
                self.vertices[i] =[(xCoord - 1) * self.scale, self.heights[z][x] * self.elevationScale, (zCoord - 1) * self.scale]

                i = i + 1

                if ((z < self.mapSize - 1) and (x < self.mapSize - 1)):
                    self.indices[t] = v
                    self.indices[t + 1] = v + self.mapSize
                    self.indices[t + 2] = v + 1
                    self.indices[t + 3] = v + 1
                    self.indices[t + 4] = v + self.mapSize
                    self.indices[t + 5] = v + self.mapSize + 1
                    v = v + 1
                    t += 6
                if (x == self.mapSize - 1):
                    v = v + 1
