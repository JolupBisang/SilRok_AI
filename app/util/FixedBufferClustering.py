import numpy as np

from .Cluster import Cluster


class FixedBufferClustering:
    def __init__(self, refer_dict: dict[str, list[np.ndarray]], MAX_SIZE=10):
        self.__clusters: dict[str, Cluster] = {}
        for key in refer_dict:
            self.__clusters[key] = Cluster(refer_dict[key], MAX_SIZE)

    def get_closest(self, vector: np.ndarray):
        similarities = {}
        for key in self.__clusters:
            similarities[key] = self.__clusters[key].similarity(vector)

        max_key = max(similarities, key=similarities.get)
        return max_key, similarities[max_key]

    def add(self, vector: np.ndarray):
        max_key, similarity = self.get_closest(vector)
        self.__clusters[max_key].add(vector)
        return max_key, similarity
