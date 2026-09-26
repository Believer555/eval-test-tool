"""
【模块定位】调度层 - 批量并发运行器
【核心功能】异步调度批量用例，控制并发数，自动执行评测并持久化结果
【设计思想】调度与执行分离，异步+信号量限流，兼顾效率与API约束
"""
import asyncio
import time
import uuid
from typing import List

from .db import TestCase, TestRun, SessionLocal
from .adapters.openai_adapter import call_openai_completion
from .metrics import evaluate_single


async def _run_single(
	tc: TestCase,
	model_conf: dict,
	use_embedding: bool = False
) -> dict:
	import json

	try:
		input_val = json.loads(tc.input) if tc.input else ""
		input_text = input_val if isinstance(input_val, str) else str(input_val)
	except Exception:
		input_text = tc.input or ""

	try:
		expected_val = json.loads(tc.expected) if tc.expected else ""
		expected_text = expected_val if isinstance(expected_val, str) else str(expected_val)
	except Exception:
		expected_text = tc.expected or ""

	loop = asyncio.get_event_loop()
	start = time.time()

	resp = await loop.run_in_executor(
		None,
		lambda: call_openai_completion(
			input_text,
			model=model_conf.get("name"),
			temperature=model_conf.get("temperature", 0.0),
			max_tokens=model_conf.get("max_tokens", 512)
		)
	)

	latency_ms = int((time.time() - start) * 1000)
	output_text = resp.get("text", "")
	metrics = evaluate_single(expected_text, output_text, use_embedding=use_embedding)
	status = "pass" if metrics.get("exact_match") else "fail"

	result = {
		"id": str(uuid.uuid4()),
		"testcase_id": tc.id,
		"model": model_conf.get("name"),
		"prompt": input_text,
		"output": output_text,
		"metrics": metrics,
		"status": status,
		"latency": latency_ms,
		"tokens": resp.get("tokens")
	}
	return result


async def run_batch(
	testcase_ids: List[str],
	model_conf: dict,
	concurrency: int = 4,
	use_embedding: bool = False
) -> List[dict]:
	session = SessionLocal()
	try:
		testcases = [session.get(TestCase, tid) for tid in testcase_ids]
		testcases = [tc for tc in testcases if tc is not None]
	finally:
		session.close()

	semaphore = asyncio.Semaphore(concurrency)
	results = []

	async def _sem_task(tc):
		async with semaphore:
			res = await _run_single(tc, model_conf, use_embedding)

			session = SessionLocal()
			try:
				run = TestRun(
					id=res["id"],
					testcase_id=res["testcase_id"],
					model=res["model"],
					prompt=res["prompt"],
					output=res["output"],
					metrics=res["metrics"],
					status=res["status"],
					latency=res["latency"],
					tokens=res["tokens"]
				)
				session.merge(run)
				session.commit()
			finally:
				session.close()

			results.append(res)

	tasks = [asyncio.create_task(_sem_task(tc)) for tc in testcases]
	await asyncio.gather(*tasks)
	return results
