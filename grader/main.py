from grader.core.context import GradingContext
from grader.core.runner import GradingRunner

def main():
    ctx = GradingContext.from_env()
    runner = GradingRunner(ctx)
    result = runner.run()
    result.write_json("grading-result.json")

if __name__ == "__main__":
    main()