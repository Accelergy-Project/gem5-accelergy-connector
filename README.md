# gem5 to Accelergy Connector

## Get started
Required packages

- Python >= 3.6
- PyYAML >= 1.1

Downloading and setting up the CLI command "accelergy" is also required. The installation for this can be found [here](https://github.com/Accelergy-Project/accelergy).

## Run an example
The `example` directory gives an example of the input and output files. It can be reproduced with the following command.

```python3 connector.py -m example/m5out -i example/input -o example/output -c example/config.yaml```

In order to reproduce reference outputs, please install
[accelergy-mcpat-plug-in](https://github.com/Accelergy-Project/accelergy-mcpat-plug-in),
[accelergy-cacti-plug-in](https://github.com/Accelergy-Project/accelergy-cacti-plug-in), and
[accelergy-aladdin-plug-in](https://github.com/Accelergy-Project/accelergy-aladdin-plug-in).

In the example run:

- mcpat estimates icache and dcache read energy
- cacti estimates icache and dcache write energy and l2 cache energy
- aladdin estimates integer fu energy

### Input Flags
- ```-m``` : specifies the gem5 m5out directory path that will be used to generate the accelergy data
- ```-i``` : specifies the directory path to put the accelergy input, for details of what this contains view the accelergy documentation.
- ```-o``` : specifies the directory path to put the accelergy output, for details of what this contains view the accelergy documentation.
- ```-c``` : specifies the config file for this conversion, detailing some misc required information

### Config File
  - hardware attributes used to specify system hardware attributes that can't be inferred from gem5
    ```
      technology: 45nm  (currently required)
      datawidth: 32     (currently required)
        ...             (additional optional attributes)
    ```
  - mapping of components to their gem5 class names so that component of a type (ie cache) can be found via this class name in the config.json within the m5out. This is currently setup with the naming of the classes present in minorCPU from gem5, and additional class names can be added to each of these lists as they come up for your architecture and based on how you name your classes in gem5.
    ```
      type_to_class_names:
        cache:
          - Cache          # Look for any component with class "Cache" and make those cache components
        off_chip_mem_ctrl:
          - DRAMCtrl       # Look for any component with class "DRAMCtrl" and make those off chip memory controllers
        mem_bus:
          - CoherentXBar   # Look for any component with class "CoherentXBar" and make those memory buses
        tlb:
          - RiscvTLB       # Look for any component with class "RiscvTLB" and make those a tlb
          ....
    ```
  - Functional unit potential paths within the cpu of the config.json from m5out. As you create your own architectures you can add their paths here, and the first found path will be used, and it is assumed there would only be a single match. If no match is found functional unit information will not be included in the output
    ```
      fu_unit_cpu_path:
        minorCPU:            # This lists the path to functional units for the gem5 minorCPU example
          - executeFuncUnits
          - funcUnits
    ```
