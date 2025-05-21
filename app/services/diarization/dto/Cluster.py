import numpy as np
from scipy.spatial.distance import cosine


class Cluster:
    def __init__(self, fixed_vectors: list[np.ndarray], MAX_SIZE=10):
        self.__MAX_SIZE = MAX_SIZE
        self.__fixed_idx = len(fixed_vectors)
        self.__vectors = fixed_vectors
        self.__update_centroid()

    def add(self, vector: np.ndarray):
        self.__vectors.append(vector)
        self.__update_centroid()
        idx = self.__get_victim_index()
        if idx:
            self.__vectors.pop(idx)

    def __get_victim_index(self):
        if len(self.__vectors) <= self.__MAX_SIZE:
            return None
        similarities = []
        for vector in self.__vectors:
            similarities.append(self.similarity(vector))
        min_index = np.argmin(similarities[self.__fixed_idx :])
        return min_index + self.__fixed_idx

    def __update_centroid(self):
        self.__centroid = np.mean(self.__vectors, axis=0)

    def similarity(self, vector: np.ndarray):
        if self.__centroid is None:
            return 1
        return 1 - cosine(self.__centroid, vector)

    @property
    def centroid(self):
        return self.__centroid
