######################################
#                                    #
# Author : Joyjit Daw                #
# Email : jdaw@nvidia.com            #
#                                    #
######################################

import argparse
from pysam import FastaFile
import vcf
import sys


def update_vcf(ref, insertions, survivor_vcf, out_vcf):
    """Update the SURVIVOR VCF file to have ref and alt sequences for each variant entry."""
    print(ref, insertions, survivor_vcf, out_vcf)
    ref = FastaFile(ref)
    insertions = FastaFile(insertions)
    
    vcf_reader = vcf.Reader(open(survivor_vcf), 'w')
    vcf_writer = vcf.Writer(open(out_vcf, 'w'), vcf_reader)
    for record in vcf_reader:
        chrom = record.CHROM
        pos = record.POS
        if record.ID.startswith("INS"):
            # Handle an INSERTION entry
            record.REF = ref.fetch(chrom, pos, pos + 1)
            survivor_insertion_key = "{}_{}".format(chrom, pos)
            record.ALT = ["{}{}".format(record.REF, insertions.fetch(survivor_insertion_key))]
        elif record.ID.startswith("DEL"):
            # Handle a DELETION entry
            svlen = record.INFO['SVLEN']
            record.REF = ref.fetch(chrom, pos, pos + svlen + 1)
            record.ALT = [ref.fetch(chrom, pos, pos + 1)]
        vcf_writer.write_record(record)

def parse_args():
    """Build parser object with options for sample."""
    parser = argparse.ArgumentParser(
        description="A VCF editing utility which adds ref and all sequences to a SURVIVOR fasta file.")

    parser.add_argument("--reference-fasta", "-r",
                        help="Reference fasta file.",
                        required=True, type=str)
    parser.add_argument("--survivor-insertions-fasta", "-i",
                        help="Insertions fasta file from SURVIVOR.",
                        required=True, type=str)
    parser.add_argument("--survivor-vcf-file", "-v",
                        help="VCF file from SURVIVOR.",
                        required=True, type=str)
    parser.add_argument("--output-vcf", "-o",
                        help="Output path of edited VCF.",
                        required=True, type=str)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    update_vcf(args.reference_fasta,
               args.survivor_insertions_fasta,
               args.survivor_vcf_file,
               args.output_vcf)
