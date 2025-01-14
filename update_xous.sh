#!/bin/bash

UPDATE_FPGA=1
UPDATE_KERNEL=1
UPDATE_LOADER=1
SKIP_PROMPT=0

for arg in "$@"
do
    case $arg in
	-k|--kernel-skip)
	    UPDATE_KERNEL=0
	    shift
	    ;;
	-l|--loader-skip)
	    UPDATE_LOADER=0
	    shift
	    ;;
	-f|--fpga-skip)
	    UPDATE_FPGA=0
	    shift
	    ;;
	-h|--help)
	    echo "$0 writes update binaries. --kernel-skip skips the kernel, --fpga-skip skips the FPGA, --loader-skip skips the loader."
	    exit 0
	    ;;
	*)
	    OTHER_ARGUMENTS+=("$1")
	    shift
	    ;;
    esac
done

md5sum ../precursors/soc_csr.bin
md5sum ../precursors/loader.bin
md5sum ../precursors/xous.img

# ensure that the power is on, this is a footgun for new users
sudo ./vbus.sh 1

sudo ./reset_soc.sh
if [ $UPDATE_LOADER -eq 1 ]
then
    cd jtag-tools && ./jtag_gpio.py -f ../../precursors/loader.bin --raw-binary -a 0x500000 -s -r -n
    cd ..
fi

if [ $UPDATE_KERNEL -eq 1 ]
then
    cd jtag-tools && ./jtag_gpio.py -f ../../precursors/xous.img --raw-binary -a 0x980000 -s -r -n
    cd ..
fi

if [ $UPDATE_FPGA -eq 1 ]
then
    cd jtag-tools && ./jtag_gpio.py -f ../../precursors/soc_csr.bin --raw-binary -a 0x280000 --spi-mode -r -n
    cd ..
    echo "Gateware update staged. To apply, select 'Install gateware update' from the root menu of your device."
    echo "If you have not initialized root keys yet, use provision_xous.sh instead to directly overwrite the image. This deletes any keys and replaces them with defaults."
fi

sudo ./reset_soc.sh
