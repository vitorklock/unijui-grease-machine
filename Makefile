.PHONY: install calibrate dispense compare notebook check

install:
	pip install -r requirements.txt

calibrate:
	python simulation/scenarios/calibration_scenario.py

dispense:
	python simulation/scenarios/dispensing_scenario.py

compare:
	python simulation/scenarios/manual_vs_auto_scenario.py

notebook:
	jupyter notebook main.ipynb

check:
	python -c "from grease_machine import AutomaticController; print('grease_machine OK')"
