import json
import yaml


def main():

    with open("data/schedule_1day.yaml", mode="r", encoding="utf-8") as in_file:
        data = yaml.safe_load(in_file)

    with open("task2/schedule_1day.json", mode="w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent="\t", ensure_ascii=False)


if __name__ == "__main__":
    main()
