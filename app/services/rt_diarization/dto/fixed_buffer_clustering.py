import numpy as np

from core import Config

from .cluster import Cluster

SAME_USER_WEIGHT = Config.get_instance().config.service.rt_diarization.same_user_weight

class FixedBufferClustering:
    def __init__(
        self, refer_dict: dict[str, list[np.ndarray]], user_id: str, MAX_SIZE=10
    ):
        self.__user_id = user_id
        self.__clusters: dict[str, Cluster] = {}
        for key in refer_dict:
            self.__clusters[key] = Cluster(refer_dict[key], MAX_SIZE)

    # 임시로 설정 함. 인식된 아이디와 오디오 아이디가 같을 때 더 큰 가중치를 줌
    def get_closest(self, vector: np.ndarray):
        similarities = {}
        for key in self.__clusters:
            weight = 1.0
            if key == self.__user_id:
                weight += SAME_USER_WEIGHT
            similarities[key] = self.__clusters[key].similarity(vector) * weight

        max_key = max(similarities, key=similarities.get)
        return max_key, similarities[max_key]

    def add(self, vector: np.ndarray):
        max_key, similarity = self.get_closest(vector)
        self.__clusters[max_key].add(vector)
        return max_key, similarity
