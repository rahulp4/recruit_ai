import json
import operator
from typing import Any, Dict, List, Union, Tuple
from difflib import SequenceMatcher
from sentence_transformers import SentenceTransformer, util
import google.generativeai as genai # NEW: Import genai for type hint

def extract_by_path_old(data: Union[dict, list], path: str):
    keys = path.split(".")
    for key in keys:
        if isinstance(data, list):
            data = [item.get(key, "") for item in data if isinstance(item, dict)]
        elif isinstance(data, dict):
            data = data.get(key, "")
        else:
            return data
    return data

def extract_by_path(data: Union[dict, list], path: str) -> Union[str, List[str]]:
    keys = path.split(".")

    def recursive_extract(d, key_chain):
        if not key_chain:
            return [d] if not isinstance(d, list) else d

        key = key_chain[0]
        rest_keys = key_chain[1:]

        results = []
        if isinstance(d, list):
            for item in d:
                results.extend(recursive_extract(item, key_chain))
        elif isinstance(d, dict):
            next_level = d.get(key, None)
            if next_level is not None:
                results.extend(recursive_extract(next_level, rest_keys))
        return results

    values = recursive_extract(data, keys)
    # Flatten and clean up
    flat_values = [v for v in values if isinstance(v, str) and v.strip()]
    return flat_values if flat_values else ""


def compute_jaccard_score(req_data: Union[str, List[str]], candidate_data: Union[str, List[str]]) -> Tuple[float, float]:
    import re

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
    # return score * 100, score * 100
    rounded = round(score * 100, 2)
    return rounded, rounded    


def compute_fuzzy_score(req_data, candidate_data) -> Tuple[float, float]:
    req_text = " ".join(req_data).lower() if isinstance(req_data, list) else str(req_data).lower()
    cand_text = " ".join(candidate_data).lower() if isinstance(candidate_data, list) else str(candidate_data).lower()
    ratio = SequenceMatcher(None, req_text, cand_text).ratio()
    # return ratio * 100, ratio * 100
    rounded = round(ratio * 100, 2)
    return rounded, rounded


def compute_operator_score(req_val, candidate_val) -> Tuple[float, float]:
    try:
        for symbol in ["<=", ">=", "<", ">", "=="]:
            if symbol in str(req_val):
                op_func = {"<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge, "==": operator.eq}[symbol]
                val = float(req_val.replace(symbol, "").strip())
                return (100.0, 100.0) if op_func(float(candidate_val), val) else (0.0, 0.0)
    except:
        pass
    return 0.0, 0.0


def compute_vector_score(model: SentenceTransformer, req_data: str, candidate_data: Union[str, List[str]]) -> Tuple[float, float]:
    print(f" req_data ",req_data)
    print(f" candidate_data ",candidate_data)
    if isinstance(candidate_data, list):
        best_score = 0.0
        for item in candidate_data:
            cand_text = str(item)
            try:
                emb1 = model.encode(req_data, convert_to_tensor=True)
                emb2 = model.encode(cand_text, convert_to_tensor=True)
                score = float(util.pytorch_cos_sim(emb1, emb2)[0][0]) * 100
                if score > best_score:
                    best_score = score
            except Exception:
                continue
        return best_score, best_score
    else:
        cand_text = str(candidate_data)
        try:
            emb1 = model.encode(req_data, convert_to_tensor=True)
            emb2 = model.encode(cand_text, convert_to_tensor=True)
            # score = float(util.pytorch_cos_sim(emb1, emb2)[0][0]) * 100
            score = round(float(util.pytorch_cos_sim(emb1, emb2)[0][0]) * 100, 2)

            return score, score
        except Exception:
            return 0.0, 0.0

def compute_vector_score_(model: SentenceTransformer, req_data: str, candidate_data: Union[str, List[str]]) -> Tuple[float, float]:
    cand_text = " ".join([str(i) for i in candidate_data]) if isinstance(candidate_data, list) else str(candidate_data)
    try:
        emb1 = model.encode(req_data, convert_to_tensor=True)
        emb2 = model.encode(cand_text, convert_to_tensor=True)
        score = float(util.pytorch_cos_sim(emb1, emb2)[0][0]) * 100
        return score, score
    except Exception:
        return 0.0, 0.0

from utils.llm_score_helper import compute_gemini_vector_score

def compute_score(model: SentenceTransformer, req_data, candidate_data, matchreq, modelgen:genai.GenerativeModel,sourcecondition="AND"):
    def score_by_type(a, b, match_type):
        if match_type == "jaccard":
            return compute_jaccard_score(a, b)
        if match_type == "fuzzy":
            return compute_fuzzy_score(a, b)
        if match_type == "operator":
            return compute_operator_score(a, b)
        if match_type == "vector":
            return compute_vector_score(model, a, b)
            # return compute_gemini_vector_score(modelgen, a, b)

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

    if isinstance(req_data, list) and isinstance(candidate_data, list):
        return score_by_type(req_data, candidate_data, matchreq)
    if isinstance(req_data, str) and isinstance(candidate_data, list):
        return score_by_type(req_data, candidate_data, matchreq)
    if isinstance(req_data, list) and isinstance(candidate_data, str):
        return score_by_type(req_data, candidate_data, matchreq)
    return score_by_type(req_data, candidate_data, matchreq)


def match_fields(model: SentenceTransformer, req_json: dict, data_json: dict,modelgen: genai.GenerativeModel):
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
            candidate_data = extract_by_path(data_json, source_path)
            if (
                candidate_data is None
                or candidate_data == ""
                or (isinstance(candidate_data, list) and not any(candidate_data))
            ):
                continue

            if isinstance(candidate_data, list) and condition == "OR":
                for idx, item in enumerate(candidate_data):
                    score, confidence = compute_score(model, rule_data, item, matchreq,modelgen, condition,)
                    all_source_scores.append({
                        "source_field": f"{source_path}[{idx}]",
                        "data": item,
                        "score": score,
                        "confidence": confidence
                    })
                continue  # Skip the final append below since it's handled per item above

            elif isinstance(candidate_data, list) and condition == "AND":
                score_sum, conf_sum, count = 0.0, 0.0, 0
                for item in candidate_data:
                    s, c = compute_score(model, rule_data, item, matchreq,modelgen, condition)
                    score_sum += s
                    conf_sum += c
                    count += 1
                score = score_sum / count if count else 0.0
                confidence = conf_sum / count if count else 0.0
            else:
                score, confidence = compute_score(model, rule_data, candidate_data, matchreq, modelgen,condition)

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

    overall_scores = calculate_overall_scores(results, req_json)
    return {
        "results": results,
        **overall_scores
    }
    # return results


def calculate_overall_scores(results: List[dict], req_json: dict) -> dict:
    total_score = 0.0
    total_weighted_score = 0.0
    total_weight = 0.0
    max_score = 0.0
    max_score_field = ""
    non_zero_scores = []

    for field_result in results:
        field_score = field_result.get("score", 0.0)
        field_name = field_result.get("field", "")
        weight = req_json.get(field_name, {}).get("weightage", 1.0)

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
        "overall_score_weighted": round(weighted_avg_score, 2),
        "overall_score_average_all": round(average_score_all_fields, 2),
        "overall_score_average_non_zero": round(average_score_non_zero_fields, 2),
        "max_score": round(max_score, 2),
        "max_score_field": max_score_field
    }

    # return {
    #     "overall_score_weighted": weighted_avg_score,
    #     "overall_score_average_all": average_score_all_fields,
    #     "overall_score_average_non_zero": average_score_non_zero_fields,
    #     "max_score": max_score,
    #     "max_score_field": max_score_field
    # }

# ✅ FUNCTION to be imported elsewhere
def run_matching_from_files(model: SentenceTransformer, req_json: dict, data_json: dict,modelgen: genai.GenerativeModel):
    return match_fields(model, req_json, data_json,modelgen)


# ---- Optional: For standalone use ----
if __name__ == "__main__":
    model = SentenceTransformer("all-MiniLM-L6-v2")
    with open("req_json_jd.json") as f:
        req_json = json.load(f)
    with open("data_json.json") as f:
        data_json = json.load(f)

    output = run_matching_from_files(model, req_json, data_json,'')
    print(json.dumps(output, indent=2))
