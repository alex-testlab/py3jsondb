import json
from typing import List
from difflib import SequenceMatcher

class JsonPath:
    def __init__(self, json_data, mode='key',fuzzy=False,thresh=0.7):
        self.data = json_data
        self.mode = mode
        self.fuzzy = fuzzy
        self.thresh = thresh

    def _fuzzy_match(self,x, against):
        """Perform a 'fuzzy' comparison between two strings.
        Returns:
            float: match percentage -- 1.0 for perfect match,
                down to 0.0 for no match at all.
        """
        return SequenceMatcher(None, x, against).ratio()


    def iter_node(self, rows, road_step, target):
        if isinstance(rows, dict):
            key_value_iter = (x for x in rows.items())
        elif isinstance(rows, list):
            key_value_iter = (x for x in enumerate(rows))
        else:
            return
        for key, value in key_value_iter:
            current_path = road_step.copy()
            current_path.append(key)
            if self.mode == 'key':
                check = key
            elif self.mode == 'value':
                check = value
            elif self.mode == 'key_value':
                check = {key:value}
                if not isinstance(target,dict):
                    raise Exception("the target should be dict when set mode to key_value")
            else:
                raise Exception("Invalid mode, should be one of key,value,key_value")
            
            if self.fuzzy:
                if self.mode=='key_value':
                    item_key = list(check.keys())[0]
                    target_key = list(target.keys())[0]
                    if item_key == target_key:
                        value = check[item_key]
                        target_value = target[target_key]
                        if isinstance(value, str):
                            score = self._fuzzy_match(value, target_value)
                            if score >= self.thresh:
                                yield current_path
                else:
                    if isinstance(check, str):
                        score = self._fuzzy_match(check, target)
                        if score >= self.thresh:
                            yield current_path
            else:
                if check == target:
                    yield current_path
            if isinstance(value, (dict, list)):
                yield from self.iter_node(value, current_path, target)

    def find_one(self, target: str) -> list:
        path_iter = self.iter_node(self.data, [], target)
        for path in path_iter:
            return path
        return []

    def find_all(self, target) -> List[list]:
        path_iter = self.iter_node(self.data, [], target)
        return list(path_iter)


