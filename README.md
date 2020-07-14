# Gem5 to Accelergy Connector
The Gem5 to Accelergy connector converts Gem5 `m5out` descriptions and statistics into the Accelergy format for power
and area estimations. Most of the components use McPat as the backend estimator.

## Get started
Required packages

- Python >= 3.6
- PyYAML >= 1.1

Downloading and setting up the CLI command "accelergy" is also required. The installation for this can be found [here](https://github.com/Accelergy-Project/accelergy).

## Run an example
The `examples` directory gives examples of the input and output files for the Gem5 in order model `MinorCPU` and the out
of order model `O3CPU`. It can be reproduced with the script `run.sh`.

In order to reproduce reference outputs, please install
[accelergy-mcpat-plug-in](https://github.com/Accelergy-Project/accelergy-mcpat-plug-in),
[accelergy-cacti-plug-in](https://github.com/Accelergy-Project/accelergy-cacti-plug-in), and
[accelergy-aladdin-plug-in](https://github.com/Accelergy-Project/accelergy-aladdin-plug-in).

## Input Flags
- ```-m``` : specifies the gem5 m5out directory path that will be used to generate the Accelergy data
- ```-i``` : specifies the directory to put the Accelergy input, for details of what this contains view the Accelergy documentation.
- ```-o``` : specifies the directory to put the Accelergy output, for details of what this contains view the Accelergy documentation.
- ```-a``` : specifies the attributes file for this conversion, detailing some misc required information
- ```-d``` : when present Accelergy will not be called
- ```-v``` : when present output will be verbose 

## Attributes File
Hardware attributes file `attributes.yaml` is used to specify system hardware attributes that can't be inferred from gem5
   
```yaml
  technology: 45nm
  datawidth: 32
```
    
## Mapping files
Mappings from Gem5 classes to Accelergy classes are specified in the `mappings` directory. Each file represents a pair
of mappings. An example from the data cache is shown below.

```python
gem5_class = "Cache"
accelergy_class = "cache"
path = "system.chip"
name_append = ""

def criteria(params):
    return params["name"] == "dcache"

constants = [
    ("n_banks", 1)
]

attributes = [
    ("size", "size"),
    ("associativity", "assoc"),
]

actions = [
    ("read_access", ["ReadReq_accesses::total"]),
    ("read_miss", ["ReadReq_misses::total"]),
    ("write_access", ["WriteReq_accesses::total"]),
    ("write_miss", ["WriteReq_misses::total"]),
]
```

When two lists of stats are supplied for an action, stats from the second list are subtracted from the first list. This
is used for instance to subtract the number of active cycles from total cycles to obtain the number of idle cycles.

## Modelled components
### Caches
All caches are modelled with the `cache` Accelergy class, with the type (`icache`, `dcache`, or `l2cache`) specified in
the `cache_type` attribute.

Supported actions: `read_access`, `read_miss`, `write_access`, `write_miss`

### Crossbar
Crossbars between levels of the memory hierarchy are modelled with the `xbar` Accelergy class.

Supported actions: `access`

### CPU functional unit
CPU functional units are modelled with the `func_unit` Accelergy class, with the type (`fpu`, `int_alu`, `mul_alu`)
specified in the `type` attribute.

Supported actions: `instruction`

### CPU register file
CPU register files are modelled with the `cpu_regfile` Accelergy component, with the type (`fp`, `int`) specified in the
`type` attribute.

Supported actions: `read`, `write`

### Tournament BP
A tournament style predictor is modelled with the `tournament_bp` Accelergy class.

Supported actions: `access`, `miss`

### TLB
TLBs for both data and instructions are modelled with the `tlb` Accelergy class.

Suppported actions: `access`, `miss`