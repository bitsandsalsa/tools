#Search for ARM ROP gadgets of an exact length. Commandline must define the following variables
#len: size, in instructions, of gadget
# e.g., awk -f test.awk -v len=2 test.asm

BEGIN {
	count = 0
	i = 0
	bad_idx = 0
}

{
	lines[++i] = $0

	# record latest bad instruction (i.e., control flow instruction in middle of gadget)
	if (/ (B|BL|BX|BLX) 0x/ || / POP .*PC/) { bad_idx = i }
}

# look for end of gadget, then print if of desired length
/ (B|BL|BX|BLX) R/ {
	if (i-bad_idx > len) {
		count++
		for (j=len; j>=0; j--) { print lines[i-j] }
		print "-----"
	}
	i = 0
	bad_idx = 0
}

END { print "Number of gadgets of length " len ": " count }
