import perlin_noise
import random
from enum import IntEnum
import numpy as np

class typeOfFallOff(IntEnum):
    Circle = 0
    Rectangle = 1
class typeOfNoise(IntEnum):
    Perlin = 0
    Simplex = 1

class NoiseSettings:
    def __init__(self, name, seed, octaves, frequency, persistence, lacunarity, Ridges, RidgesStrength, Turbulance, typeOfNoise):
        self.name = name
        self.seed = seed
        self.octaves = octaves
        self.frequency = frequency
        self.persistence = persistence
        self.lacunarity = lacunarity
        self.Ridges = Ridges
        self.RidgesStrength = RidgesStrength
        self.Turbulance = Turbulance
        self.typeOfNoise = typeOfNoise
        self.layerActive = True
        self.useFirstLayerAsMask = False

def Noise(x, z, noiseSettings: NoiseSettings, mapSize):
    tmpAmplitude = 1.0
    tmpFrequency = noiseSettings.frequency
    height = 0.0

    gridSize = mapSize
    random.seed(noiseSettings.seed)
    perlinNoise = perlin_noise.PerlinNoise(seed=noiseSettings.seed)

    for i in range(0, noiseSettings.octaves, 1):
        xCoord = (x * tmpFrequency / gridSize) + random.randrange(-10000, 10000)
        zCoord = (z * tmpFrequency / gridSize) + random.randrange(-10000, 10000)
        distFromCenter = 0

        if (noiseSettings.typeOfNoise == typeOfNoise.Perlin):
            t = (xCoord, zCoord)
            distFromCenter = (perlin_noise.PerlinNoise.noise(perlinNoise, coordinates=t))
            #case typeOfNoise.Simplex:
            #distFromCenter = noise.snoise(new float2(xCoord, zCoord));
        if (noiseSettings.Turbulance):
            distFromCenter = np.abs(distFromCenter)
        if (noiseSettings.Ridges):
            distFromCenter = 1 - distFromCenter
            distFromCenter = np.pow(distFromCenter, noiseSettings.RidgesStrength)
        height += distFromCenter * tmpAmplitude
        tmpFrequency *= noiseSettings.lacunarity
        tmpAmplitude *= noiseSettings.persistence
        
    return height