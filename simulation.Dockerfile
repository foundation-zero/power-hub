FROM mwalbeck/python-poetry:1-3.12
COPY . /var/energy-box-control
WORKDIR /var/energy-box-control
RUN poetry install --only main
WORKDIR energy_box_control
CMD ["poetry", "run", "run_power_hub_simulation"]
