#### Nellie's Notes

In the example run:

  - ichache and decache is estimated by both the mcpat plug-in and cacti plug-in
     - mcpat can estimate the read access energy numbers, but not write

  - l2 cache is estimated by cacti

  - floating point units
    - if you do not have aladdin plug-in installed, the integer operations should have output energy of 1
      just as presented in the reference. These estimations are performed by dummy plug-in
    - if you do have aladdin plug-in installed, you should get the following in ERT:
     
      ```
      - name: system_arch.chip.exec
        actions:
        - name: int_instruction
          arguments: null
          energy: 0.086
        - name: mul_instruction
          arguments: null
          energy: 8.63
        - name: fp_instruction
          arguments: null
          energy: 23.73
      ```