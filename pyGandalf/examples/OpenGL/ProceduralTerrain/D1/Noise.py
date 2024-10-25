import perlin_noise
import random
from enum import Enum
import numpy as np

"""Perlin noise implementation."""
# Licensed under ISC
from itertools import product
import math
import random

class typeOfFallOff(Enum):
    Circle = 1
    Rectangle = 2
class typeOfNoise(Enum):
    Perlin = 1
    Simplex = 2

class NoiseSettings:
    def __init__(self, seed, octaves, frequency, persistence, lacunarity, Ridges, RidgesStrength, Turbulance, typeOfNoise):
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

def Noise(x, z, noiseSettings, mapSize):
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

        if(noiseSettings.typeOfNoise == typeOfNoise.Perlin):
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