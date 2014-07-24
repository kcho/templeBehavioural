#!/Users/admin/anaconda/bin/python
import unicodedata
import re
import codecs
import os
import csv
import argparse
import textwrap
import pandas as pd
import numpy as np

def findBehaviourDir(directory):

    # find 'Behavior_Data'
    behaviourDir=[]
    for root,dirs,files in os.walk(directory):
        if re.search('Behavior_Data',root):
            print root
            behaviourDir.append(root)

    return behaviourDir


def main(args):

    behaviourDirs = findBehaviourDir(os.path.abspath(args.directory))
    tables = readTables(behaviourDirs)
    mergedDf = tables2Df(tables)
    toExcel(mergedDf)

def tables2Df(tables):
    init=pd.DataFrame()
    for dictWithMean in tables:
        # dictionary into dataframe
        df=pd.DataFrame.from_dict(dictWithMean)

        # set index names
        df.index=['ACC','RT','subjectName','timeline']

        # transpose the table
        df = df.T

        # name them
        df.index = pd.MultiIndex.from_arrays([[x[0] for x in df.index],
            [x[1] for x in df.index]],names=['Run','Detail'])

        # initialise the index
        dfIndexReset = df.reset_index()

        # pivot table
        pivotTable = pd.pivot_table(dfIndexReset,
                                    values=['ACC','RT'],
                                    cols=['Run'],
                                    rows=['subjectName','timeline','Detail'],
                                    aggfunc=np.sum)

        # column name set
        pivotTable.columns.names=['value','Run']

        # value column to index
        table = pivotTable.stack('value')

        # swaplevels of the index
        table.index = table.index.swaplevel(2,3)

        # order index
        table = table.sortlevel()

        # adding average
        table['average'] = table.T.mean()

        # merging
        init = pd.concat([init,table])

    return init


def readTables(behaviourDirs):
    tables = []
    # for each behaviourDirs
    for behaviourDir in behaviourDirs:
        # get subject name
        subjectName = re.search('((MED|CON)\d{2})',behaviourDir).group(1)
        # get timeline
        timeline = re.search('(pre|post)',behaviourDir).group(1)
        # find log texts
        textList = [os.path.join(behaviourDir,x) for x in os.listdir(behaviourDir) if re.search('Temple.*txt$',x)]

        # for each log text
        # make a directory
        dictWithMean = {}
        for text in textList:
            # get information such as ...
            # dictionary = {'correct':correctTrials,
                    #'wrong':wrongTrials,
                    #'cong':congruent,
                    #'incong':incongruent,
                    #'spatial':spatial,
                    #'alert':alert,
                    #'noQue':noQue}
            dictionary = getInfo(text)

            for name,trialTexts in dictionary.iteritems():
                mean = getMean(trialTexts)
                dictWithMean[(os.path.basename(text)[-5],name)]=(
                        len(trialTexts),mean,subjectName,timeline,)
        tables.append(dictWithMean)
    return tables


def toExcel(mergedDf):
    mergedDf.index = pd.MultiIndex.from_tuples(mergedDf.index)
    #print mergedDf.head()
    mergedDf.index.names=['subject','timeline','variable','condition']

    mergedDf = mergedDf.sortlevel(level=1,ascending=False,sort_remaining=False).sortlevel(level=0,sort_remaining=False)
    #print mergedDf.index.sortlevel(level=1)

    writer = pd.ExcelWriter('/Volumes/promise/CCNC_SNU_temple_2014/3_dataSpreadSheet/behaviour.xlsx')
    mergedDf.to_excel(writer,'Sheet1')
    writer.save()

def getMean(trialTexts):
    value = 0
    #print len(trialTexts)
    for trialText in trialTexts:
        #print trialText
        #print int(re.search('SlideTarget.RT: (\d+)',trialText).group(1))

        value += float(re.search('SlideTarget.RT: (\d+)',trialText).group(1))
    try:
        value = value/len(trialTexts)
    except:
        value = 0
    return value


def getInfo(textFile):
    #print textFile
    #print '='*25
    #with codecs.open(textFile, encoding='utf-16') as f, open('output.csv', 'w') as fout:
        #text = f.read()
    with codecs.open(textFile, encoding='utf-16') as f:
        text = f.read()

    #total trials
    textSplit = text.split('*** LogFrame Start ***')

    #correct trials only
    correctTrials = [x for x in textSplit if re.search('SlideTarget.ACC: 1',x)]
    #print 'correct : {0}'.format(len(correctTrials))
    wrongTrials = [x for x in textSplit if re.search('SlideTarget.ACC: 0',x)]

    #for less than 2000
    lessThan2000 = [x for x in correctTrials if int(re.search('SlideTarget.RT: (\d+)',x).group(1)) < 2000]

    congruent = [x for x in lessThan2000 if 'FlankingType: congruent' in x]
    incongruent = [x for x in lessThan2000 if 'FlankingType: incongruent' in x]
    spatial = [x for x in lessThan2000 if 'CuePositionY: 270' in x or 'CuePositionY: 210' in x]
    alert = [x for x in lessThan2000 if 'CuePositionY: 240' in x]
    noQue = [x for x in lessThan2000 if 'CuePositionY: -100' in x]

    #dictionary = {'correct':correctTrials,
            #'wrong':wrongTrials,
            #'cong':congruent,
            #'incong':incongruent,
            #'spatial':spatial,
            #'alert':alert,
            #'noQue':noQue}

    #without correct / wrong list
    dictionary = {'cong':congruent,
            'incong':incongruent,
            'spatial':spatial,
            'alert':alert,
            'noQue':noQue}
    return dictionary



if __name__=='__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
            description = textwrap.dedent('''\
                    {codeName} : Pre-process the new diffusion tensor images
                    ==========================================================
                        eg) {codeName}
                        eg) {codeName} --dir /Users/kevin/NOR04_CKI
                        eg) {codeName} --dir /Users/kevin/NOR04_CKI
                    '''.format(codeName=os.path.basename(__file__))))
    parser.add_argument('-dir','--directory',help='Data directory location', default=os.getcwd())
    args = parser.parse_args()
    main(args)

