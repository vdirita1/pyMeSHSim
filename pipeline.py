#!/usr/bin/python3
import sys, os
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

from pyMeSHSim.data.createData import createBcolzData
from pyMeSHSim.data.duiFunc import duiFunc
from pyMeSHSim.data.dataInterface import dataHandle
from pyMeSHSim.metamapWrap.MetamapInterface import MetaMap
from pyMeSHSim.metamapWrap.Concept import Concept
from pyMeSHSim.Sim.MeSHProcess import MeSHProcess
from pyMeSHSim.Sim.similarity import termComp
from pyMeSHSim.Sim.similarity import metamapFilter



        
class pipeline(object):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description='an example to parse free text and claculate semantic similarity',
            usage='''pipeline.py <command> [<args>]

            The most commonly used commands are:
                textParse     parsing free text from free text
                simCal      calculating similarity fom MeSH terms
            ''')
        parser.add_argument('command', help='Subcommand to run')
        # parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print ('ERROR: Unrecognized command')
            parser.print_help()
            exit(1)
        # use dispatch pattern to invoke method with same name
        getattr(self, args.command)()

    def textParse(self):
        parser = argparse.ArgumentParser(
            description='Parse the free text')
        # prefixing the argument with -- means it's optional
        parser.add_argument('metamapPath', type=str, help='the path where metamap installed.')
        parser.add_argument('inputFile', type=str, help='the file containing free text to be parsed.')
        parser.add_argument('out_prefix', type=str, help='out_prefix.')
        parser.add_argument('--semantic_type', '-J', type=str, help='the semantic including in text processing. the value is "disease" or "all", if define this parameter by your own, pelease separate by commas',  default="disease")
        parser.add_argument('--source', '-R', type=str, help='the vocabulary source used to do text parsing. if you want select more than one source, sperate it by commas', default="MSH")
        parser.add_argument('--short', action='store_true', help='flag if you are parsing short sentence.')
        # now that we're inside a subcommand, ignore the first
        # TWO argvs, ie the command (git) and the subcommand (textParse)
        args = parser.parse_args(sys.argv[2:])
        print ('Running pipeline textParsing')
        #format_file = format_free_text(input_file=args.inputFile)
        parseText(metamap_path=args.metamapPath, input_file=args.inputFile, output_dir=args.out_prefix, source=args.source, semantic_type = args.semantic_type, short=args.short)

    def simCal(self):
        parser = argparse.ArgumentParser(
            description='calculating semantic similarity of MeSH terms')
        # NOT prefixing the argument with -- means it's not optional
        parser.add_argument('input_file')
        parser.add_argument('out_prefix', type=str, help='out_prefix.')
        parser.add_argument('--weight', '-w', type=float, help='the weight of wang method', default=0.7)
        args = parser.parse_args(sys.argv[2:])
        print ('Running pipeline.py sim ')
        calSim(input_file=args.input_file, output_dir=args.out_prefix, weight=args.weight)

def format_free_text(input_file=None):
    output_file_path = ".".join(input_file.split(".")[:-1]) + ".reFormat.txt"
    new_file = open(output_file_path, "w")
    i = 0
    handle = open(input_file, "r")
    for line in handle:
        i = i + 1
        item = line.strip("\n\r")
        new_file.write(str(i) + "|" + item + "\n")
    handle.close()
    new_file.close()
    return output_file_path
        
def parseText(metamap_path=None, input_file=None, output_dir=None, source=None, semantic_type=None, short=None):
    metamap = MetaMap(path=metamap_path)
    skrmedpostctl=os.path.join(os.path.dirname(metamap_path), "skrmedpostctl")
    wsdserverctl=os.path.join(os.path.dirname(metamap_path), "wsdserverctl")
    #os.system(skrmedpostctl + "\t" + "start")
    #os.system(wsdserverctl + "\t" + "start")
    
    handle = open(input_file, "r")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = os.path.join(output_dir, "parsing_result.txt")
    outputfile = open(output_path, "w")

    #argument initialize
    if semantic_type == "disease":
        semantic_type = metamap.semanticTypes
    elif semantic_type == "all":
        semantic_type = None
    else:
        semantic_type = semantic_type.split(",")

    source_list = source.split(",")
    source = source_list
    if short is False:
        conjunction = False
        term_processing = False
    else:
        conjunction = True
        term_processing = True

    for line in handle:
        array = line.strip("\n\r").split("|")
        if len(array) != 2:
            print("Error: the input file format is wrong!")
            exit(1)
        id_str = array[0]
        text_phrase = array[1].strip('"')
        
        #run
        conceptMeSHItem = None 
        conceptMeSHItem = metamap.runMetaMap(text=text_phrase, semantic_types=semantic_type, conjunction=conjunction, term_processing=term_processing)
        
        if conceptMeSHItem == []:
            continue
        
        filter = metamapFilter(path=metamap_path)
        conceptMeSHItem = filter.discardAncestor(concepts=conceptMeSHItem)
        meshidList = []
        for i in conceptMeSHItem:
            if i["MeSHID"] is None:
                continue
            meshidList.append(i["MeSHID"])
        if len(meshidList) > 1:
            meshStr = ",".join(meshidList)
        else:
            meshStr = i["MeSHID"]
        outputfile.write("%s\t%s\t%s\n" % (id_str, text_phrase, meshStr))
    outputfile.close()
    handle.close()
    return output_path

def calSim(input_file=None, output_dir=None, weight=None):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    term_1, term_2 = "D009765", "D001835"
    df = pd.read_csv(input_file, names=["term_1", "term_2"], sep="\t")
    output_path = os.path.join(output_dir, "similarity_result_weight_" + str(weight) +".txt")
    outputfile = open(output_path, "w")
    for idx, row in df.iterrows():
        [lin, res, jiang, rel, wang] = calculate_sim(dui1=row["term_1"], dui2=row["term_2"], weight=weight)
        outputfile.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (row["term_1"], row["term_2"], round(lin, 2), round(res, 2), round(jiang, 2), round(rel, 2), round(wang, 2)))
    outputfile.close()
    return output_path


def calculate_sim(dui1=None, dui2=None, weight=None):
    simCom = termComp()
    ty1 = simCom.getCategory(dui=dui1)
    ty2 = simCom.getCategory(dui=dui2)
    lin, res, jiang, rel, wang = 0, 0, 0, 0, 0
    for cat1 in ty1:
        for cat2 in ty2:
            if cat1 == cat2:
                (res_tmp, lin_tmp, jiang_tmp, rel_tmp) = simCom.simil(dui1=dui1, dui2=dui2, category=cat1)
                wang_tmp = simCom.termSim(dui1=dui1, dui2=dui2, method="wang", category=cat1, weight=weight)
                if lin < lin_tmp: lin = lin_tmp
                if res < res_tmp: res = res_tmp
                if jiang < jiang_tmp: jiang = jiang_tmp
                if rel < rel_tmp: rel = rel_tmp
                if wang < wang_tmp: wang = wang_tmp
    return [lin, res, jiang, rel, wang]
    







if __name__ == '__main__':
    pipeline()
    """
    ./pipeline.py textParse /home/luozhihui/Software/public_mm/bin/metamap16 ./output_dir/free_text.reFormat.txt ./output_dir --source=MSH --short
    ./pipeline.py simCal ./output_dir/MeSH_term_pair.txt ./output_dir --weight=0.7
    """
