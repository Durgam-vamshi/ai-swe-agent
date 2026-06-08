from app.agent.retry_loop import run_agent

base_path = "./test_repo"
file_name = None

issue = "NameError: x is not defined"

result = run_agent(base_path, file_name, issue)

print("\n✅ FINAL RESULT:\n")
print(result)