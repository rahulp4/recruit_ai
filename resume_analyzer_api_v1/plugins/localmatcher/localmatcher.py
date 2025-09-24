import json
import operator
import re
from typing import Any, Dict, List, Union, Tuple
from difflib import SequenceMatcher
from sentence_transformers import SentenceTransformer, util
from functools import lru_cache

class ProfileMatcher:
    # def __init__(self, model_name="all-MiniLM-L6-v2"):
    #     # self.model = SentenceTransformer(model_name)

    # @lru_cache(maxsize=2048)
    # def cached_encode(self, text: str):
    #     return self.model.encode(text, convert_to_tensor=True)

    def extract_by_path(self, data: Union[dict, list], path: str):
        keys = path.split(".")
        for key in keys:
            if isinstance(data, list):
                data = [item.get(key, "") for item in data if isinstance(item, dict)]
            elif isinstance(data, dict):
                data = data.get(key, "")
            else:
                return data
        return data

    def compute_jaccard_score(self, req_data: Union[str, List[str]], candidate_data: Union[str, List[str]]) -> Tuple[float, float]:
        def tokenize(text):
            text = str(text).lower()
            text = re.sub(r"[^\w\s]", "", text)
            return set(text.split())

        req_tokens = set()
        if isinstance(req_data, list):
            for item in req_data:
                req_tokens |= tokenize(item)
        else:
            req_tokens = tokenize(req_data)

        cand_tokens = set()
        if isinstance(candidate_data, list):
            for item in candidate_data:
                cand_tokens |= tokenize(item)
        else:
            cand_tokens = tokenize(candidate_data)

        if not req_tokens or not cand_tokens:
            return 0.0, 0.0

        intersection = req_tokens & cand_tokens
        union = req_tokens | cand_tokens
        score = len(intersection) / len(union)
        return score * 100, score * 100

    def compute_fuzzy_score(self, req_data, candidate_data) -> Tuple[float, float]:
        req_text = " ".join(req_data).lower() if isinstance(req_data, list) else str(req_data).lower()
        cand_text = " ".join(candidate_data).lower() if isinstance(candidate_data, list) else str(candidate_data).lower()
        ratio = SequenceMatcher(None, req_text, cand_text).ratio()
        return ratio * 100, ratio * 100

    def compute_operator_score(self, req_val, candidate_val) -> Tuple[float, float]:
        try:
            for symbol in ["<=", ">=", "<", ">", "=="]:
                if symbol in str(req_val):
                    op_func = {
                        "<": operator.lt, "<=": operator.le,
                        ">": operator.gt, ">=": operator.ge,
                        "==": operator.eq
                    }[symbol]
                    val = float(req_val.replace(symbol, "").strip())
                    return (100.0, 100.0) if op_func(float(candidate_val), val) else (0.0, 0.0)
        except:
            pass
        return 0.0, 0.0

    def compute_vector_score(self,model:SentenceTransformer, req_data: str, candidate_data: Union[str, List[str]]) -> Tuple[float, float]:
        cand_text = " ".join([str(i) for i in candidate_data]) if isinstance(candidate_data, list) else str(candidate_data)
        try:
            emb1 = self.model.encode(req_data, convert_to_tensor=True)
            emb2 = self.model.encode(cand_text, convert_to_tensor=True)
            score = float(util.pytorch_cos_sim(emb1, emb2)[0][0]) * 100
            return score, score
        except Exception:
            return 0.0, 0.0

    def compute_score(self, model,req_data, candidate_data, matchreq, sourcecondition="AND") -> Tuple[float, float]:
        def score_by_type(a, b, match_type):
            if match_type == "jaccard": return self.compute_jaccard_score(a, b)
            if match_type == "fuzzy": return self.compute_fuzzy_score(a, b)
            if match_type == "operator": return self.compute_operator_score(a, b)
            if match_type == "vector": return self.compute_vector_score(model,a, b)
            return 0.0, 0.0

        req_list = req_data if isinstance(req_data, list) else [req_data]
        cand_list = candidate_data if isinstance(candidate_data, list) else [candidate_data]

        if sourcecondition == "OR":
            best_score, best_conf = 0.0, 0.0
            for req in req_list:
                for cand in cand_list:
                    score, conf = score_by_type(req, cand, matchreq)
                    if score > best_score:
                        best_score, best_conf = score, conf
            return best_score, best_conf

        # AND logic (default)
        return score_by_type(req_data, candidate_data, matchreq)

    def match_fields(self, model,req_json: dict, data_json: dict):
        results = []
        for field, rule in req_json.items():
            if not isinstance(rule, dict):
                continue
            matchreq = rule.get("matchreq")
            sources = rule.get("profiledatasource") or rule.get("reqField", [])
            rule_data = rule.get("data", "")
            condition = (rule.get("sourcecondition") or "AND").upper()
            all_source_scores = []

            for source_path in sources:
                candidate_data = self.extract_by_path(data_json, source_path)

                if candidate_data in [None, ""] or (isinstance(candidate_data, list) and not any(candidate_data)):
                    continue

                score, confidence = 0.0, 0.0

                if isinstance(candidate_data, list) and condition == "OR":
                    score, confidence = max(
                        (self.compute_score(model,rule_data, item, matchreq, condition) for item in candidate_data),
                        default=(0.0, 0.0)
                    )

                elif isinstance(candidate_data, list) and condition == "AND":
                    score_sum, conf_sum, count = 0.0, 0.0, 0
                    for item in candidate_data:
                        s, c = self.compute_score(model, rule_data, item, matchreq, condition)
                        score_sum += s
                        conf_sum += c
                        count += 1
                    score = score_sum / count if count else 0.0
                    confidence = conf_sum / count if count else 0.0

                else:
                    score, confidence = self.compute_score(model,rule_data, candidate_data, matchreq, condition)

                all_source_scores.append({
                    "source_field": source_path,
                    "data": candidate_data,
                    "score": score,
                    "confidence": confidence
                })

            best_match = max(all_source_scores, key=lambda x: x["score"], default={})
            results.append({
                "field": field,
                "score": best_match.get("score", 0.0),
                "confidence": best_match.get("confidence", 0.0),
                "best_source_used": best_match.get("source_field", ""),
                "req_data": rule_data,
                "sources_evaluated": all_source_scores
            })

        overall_scores = self.calculate_overall_scores(results, req_json)
        return {
            "results": results,
            **overall_scores
        }

        # return results

    def calculate_overall_scores(self, results: List[dict], req_json: dict) -> dict:
        total_score = 0.0
        total_weighted_score = 0.0
        total_weight = 0.0
        max_score = 0.0
        max_score_field = ""
        non_zero_scores = []

        for field_result in results:
            field_score = field_result.get("score", 0.0)
            field_name = field_result.get("field", "")
            weight = req_json.get(field_name, {}).get("weight", 1.0)

            total_score += field_score
            total_weighted_score += field_score * weight
            total_weight += weight

            if field_score > max_score:
                max_score = field_score
                max_score_field = field_name

            if field_score > 0.0:
                non_zero_scores.append(field_score)

        average_score_all_fields = total_score / len(results) if results else 0.0
        average_score_non_zero_fields = sum(non_zero_scores) / len(non_zero_scores) if non_zero_scores else 0.0
        weighted_avg_score = total_weighted_score / total_weight if total_weight > 0 else 0.0

        return {
            "overall_score_weighted": weighted_avg_score,
            "overall_score_average_all": average_score_all_fields,
            "overall_score_average_non_zero": average_score_non_zero_fields,
            "max_score": max_score,
            "max_score_field": max_score_field
        }