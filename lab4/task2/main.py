import json
import yaml


if __name__ == "__main__":

    with open("data/schedule_1day.yaml", mode="r", encoding="utf-8") as in_file:
        data = yaml.safe_load(in_file)

    with open("task2/output_schedule_1day.json", mode="w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)
