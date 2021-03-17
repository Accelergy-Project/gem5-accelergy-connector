# Gem5 to Accelergy Connector
The Gem5 to Accelergy connector `connector.py` converts Gem5 `m5out` descriptions and statistics into the Accelergy format for power
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
- ```-m``` : Specifies the gem5 m5out directory path that will be used to generate the Accelergy data.
- ```-i``` : Specifies the directory to put the Accelergy input, for details of what this contains view the Accelergy documentation.
- ```-o``` : Specifies the directory to put the Accelergy output, for details of what this contains view the Accelergy documentation.
- ```-a``` : Specifies the attributes file for this conversion, detailing some required information.
- ```-d``` : Debug flag. When present Accelergy will not be called.
- ```-v``` : Verbose flag. When present output will give details of component mappings.

## Attributes File
Hardware attributes file `attributes.yaml` is used to specify system hardware attributes that can't be inferred from gem5.
An example is shown below.
   
```yaml
technology: 45nm
datawidth: 32
device_type: lop
```

The device type can be any of the following:

- High Power `hp`
- Low Operating Power `lop`
- Low Standby Power `lstp`

These correspond to the device types defined by the International Technology Roadmap for Semiconductors (ITRS), and is
used by McPat for its energy estimations.
    
## Mapping files
Mappings from Gem5 classes to Accelergy classes are specified in the `mappings` directory. Each file represents a pair
of mappings. An example for the data cache is shown below.

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

The connector script `connector.py` will generate an accelergy component at path `path` for every matching
gem5 class in the `config.json` file where `criteria(params)` evaluates to true. The mapping does not have to be
one-to-one. It may be many-to-one or one-to-many as is the case for the gem5 class `DerivO3CPU` which corresponds to
a number of accelergy components.


The parameters for attributes corresponds to the keys in `config.json` and the parameters for actions corresponds to
the action count entry in `stats.txt`. When two lists of parameters are supplied for an action, the total of the second
list is subtracted from the total of the first list. This is used for instance to subtract the number of active cycles
from total cycles to obtain the number of idle cycles (for an example see `mappings/DerivO3CPU_fpu.py`).

## Modelled components

### Branch predictor

> Gem5 class: TournamentBP
>
> Accelergy class: tournament_bp
>
> Actions: `hit`, `miss`

Branch predictor modelled by McPat.

### Branch target buffer

> Gem5 class: TournamentBP
>
> Accelergy class: btb
>
> Actions: `read`, `write`

Branch target buffer modelled by McPat.

### Cache

> Gem5 class: Cache
>
> Accelergy class: cache
>
> Actions: `read_access`, `read_miss`, `write_access`, `write_miss`

Cache modelled by McPat. The cache type (`icache`, `dcache`, `l2cache`) is specified in the `cache_type` attribute.

### Crossbar

> Gem5 class: CoherentXBar
>
> Accelergy class: xbar
>
> Actions: `access`

Crossbar modelled by McPat.

### Decoder

> Gem5 class: DerivO3CPU
>
> Accelergy class: decoder
>
> Actions: `access`

Decoder modelled by McPat.

### DRAM

> Gem5 class: DRAMCtrl
>
> Accelergy class: DRAM
>
> Actions: `read`, `write`, `idle` 

DRAM modelled by Cacti as LPDDR.

### Fetch buffer

> Gem5 class: DerivO3CPU
>
> Accelergy class: fetch_buffer
>
> Actions: `access`

Fetch buffer modelled by McPat.

### Function unit

> Gem5 class: DerivO3CPU, MinorCPU
>
> Accelergy class: func_unit
>
> Actions: `access`, `idle`

Functional unit modelled by McPat. The type (`fpu`, `int_alu`, `mul_alu`) is specified in the `type` attribute.

### Instruction queue

> Gem5 class: DerivO3CPU
>
> Accelergy class: inst_queue
>
> Actions: `read`, `write`, `wakeup`

Instruction queue modelled by McPat. The type (`int`, `fp`) is specified in the `type` attribute.

### Load store queue

> Gem5 class: DerivO3CPU
>
> Accelergy class: load_store_queue
>
> Actions: `load`, `store`

Load store queue modelled by McPat. The type (`load`, `store`) is specified in the `type` attribute.

### Register file

> Gem5 class: DerivO3CPU, MinorCPU
>
> Accelergy class: cpu_regfile
>
> Actions: `read`, `write`

Register file modelled by McPat. The type (`int`, `fp`) is specified in the `type` attribute.

### Renaming unit

> Gem5 class: DerivO3CPU
>
> Accelergy class: renaming_unit
>
> Actions: `read`, `write`

Renaming unit modelled by McPat.

### Reorder buffer

> Gem5 class: DerivO3CPU
>
> Accelergy class: reorder_buffer
>
> Actions: `read`, `write`

Reorder buffer modelled by McPat.

### Translation lookaside buffer

> Gem5 class: RiscvTLB
>
> Accelergy class: tlb
>
> Actions: `hit`, `miss`

Translation lookaside buffer modelled by McPat.
