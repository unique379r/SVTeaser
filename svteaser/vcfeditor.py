######################################
#                                    #
# Author : Joyjit Daw                #
# Email : jdaw@nvidia.com            #
#                                    #
######################################

import re
import sys
import logging
import argparse

from tempfile import NamedTemporaryFile

import pysam
import truvari

def correct_survivor_vcf(in_vcf):
    """
    Correct survivor vcf mistakes so it's parsable by pysam.VariantFile
    Returns the name of the temporary file that's c
    """
    extra_header = "\n".join(['##FILTER=<ID=LowQual,Description="Default. Manual">',
                          '##INFO=<ID=PRECISE,Number=1,Type=Flag,Description="Some type of flag">'])

    temp_file = NamedTemporaryFile(suffix=".vcf", mode='w', delete=False) 
    with open(in_vcf, 'r') as fh:
        for line in fh:
            if line.startswith("##"):
                temp_file.write(line)
                continue
            if line.startswith("#CHROM"):
                temp_file.write(extra_header + '\n')
                line = line.strip() + "\tSAMPLE\n"
                temp_file.write(line)
                continue
            line = re.sub(":GL:GQ:FT:RC:DR:DV:RR:RV", "", line)
            line = re.sub("LowQual", ".", line)
            temp_file.write(line)
    temp_file.close()
    return temp_file.name

def update_vcf(ref, insertions, survivor_vcf, out_vcf):
    """Update the SURVIVOR VCF file to have ref and alt sequences for each variant entry.

    e.g. If a variant entry has the following VCF description

    "chr1   10  INS001  N   <INS>   .   LowQual SVLEN=10"

    Then the entry will be updated with data from ref and insertions fasta to look like

    "chr1   10  INS001  A   ATTTTTTTTTTGGGGGGGGGG   .   LowQual SVLEN=10"

    Args:
        ref : Path to reference fasta file.
        insertions : Path to SURVIVOR insertions fasta file.
        survivor_vcf : Path to SURVIVOR simulated VCF file.
        out_vcf : Putput path for updated SURVIVOR VCF.
    """
    survivor_vcf = correct_survivor_vcf(survivor_vcf)
    logging.info(" ".join([ref, insertions, survivor_vcf, out_vcf]))
    ref = pysam.FastaFile(ref)
    insertions = pysam.FastaFile(insertions)
    
    vcf_reader = pysam.VariantFile(survivor_vcf)
    header = vcf_reader.header
    vcf_writer = pysam.VariantFile(out_vcf, 'w', header=header)
    for record in vcf_reader:
        record = truvari.copy_entry(record, header)
        chrom = record.chrom
        pos = record.pos
        if record.id.startswith("INS"):
            # Handle an INSERTION entry
            record.ref = ref.fetch(chrom, pos, pos + 1)
            survivor_insertion_key = "{}_{}".format(chrom, pos)
            record.alts = ["{}{}".format(record.ref, insertions.fetch(survivor_insertion_key))]
        elif record.id.startswith("DEL"):
            # Handle a DELETION entry
            svlen = record.info['SVLEN']
            record.ref = ref.fetch(chrom, pos, pos + svlen + 1)
            record.alts = [ref.fetch(chrom, pos, pos + 1)]
        else: # just in case inversions or something get through
            continue
        vcf_writer.write(record)

def parse_args():
    """Build parser object with options for sample.

    Returns:
        Python argparse parsed object.
    """
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