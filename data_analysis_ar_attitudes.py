from sqlalchemy import create_engine, MetaData, Table
import json
import pandas as pd
import scipy.stats as stats
import matplotlib
matplotlib.use('tkagg')
import matplotlib.pyplot as plt
import scipy.stats as stats
import statsmodels.api as sm
import statsmodels.formula.api as ols
from pingouin import pairwise_tukey
import pingouin as pg
import copy
import seaborn as sns
import numpy as np
import os

'''
CONSTANTS and FLAGS
'''

FLAG_EXPORT = False

FILENAME_OUTPUTS = "outputs/"
FILENAME_PLOTS = FILENAME_OUTPUTS + "plots/"
FILENAME_ANOVAS = FILENAME_OUTPUTS + "anovas/"

OUTPUT_GRAPH_BOXPLOT = True
OUTPUT_GRAPH_STRIPPLOT = True
OUTPUT_GRAPH_BLENDED = True
OUTPUT_CALC_ANOVA = True

# For reference, the columns of the input are:
# columns = 'StartDate', 'EndDate', 'Status', 'Progress', 'Duration (in seconds)',
#        'Finished', 'RecordedDate', 'ResponseId', 'DistributionChannel',
#        'UserLanguage', 'Q_RecaptchaScore', 'Q72', 'Q70', 'Q19', 'Q9', 'Q10',
#        'Q35', 'Q26', 'Q27', 'Q46', 'Q37', 'Q38', 'Q59_1', 'Q59_2', 'Q59_3',
#        'Q62_1', 'Q62_2', 'Q62_3', 'Q73_1', 'Q73_2', 'Q73_3', 'Q63_1', 'Q63_2',
#        'Q63_3', 'Q64_1', 'Q64_2', 'Q64_3', 'Q75_1', 'Q75_2', 'Q75_3', 'Q65_1',
#        'Q65_2', 'Q65_3', 'Q66_1', 'Q66_2', 'Q66_3', 'Q74_1', 'Q74_2', 'Q74_3',
#        'Q67_1', 'Q67_2', 'Q67_3', 'Q68_1', 'Q68_2', 'Q68_3', 'Q69_1', 'Q69_2',
#        'Q69_3', 'Q72_1', 'Q72_2', 'Q72_3', 'Q70_1', 'Q70_2', 'Q70_3',
#        'Q74_1.1', 'Q74_2.1', 'Q74_3.1', 'Q73_1.1', 'Q73_2.1', 'Q73_3.1',
#        'Q73_4', 'Q77', 'Q92_1', 'Q92_2', 'Q92_3', 'Q86', 'Q76', 'Q96', 'Q98',
#        'Q94', 'Q107', 'Q1_28', 'Q2', 'Q2_11_TEXT', 'Q3', 'Q111', 'Q5']

mapping = {}
mapping['Extremely uncomfortable']                  = -2
mapping['Somewhat uncomfortable']                   = -1
mapping['Neither comfortable nor uncomfortable']    = 0
mapping['Somewhat comfortable']                     = 1
mapping['Extremely comfortable']                    = 2

COL_CONSENT     = 'Q72'
COL_PROLIFIC_ID = 'Q70'
COL_DURATION    = 'Duration (in seconds)'
COL_ID          = 'ResponseId'

COL_USE_SNAP    = 'Q19'
COL_USE_WARBY   = 'Q26'
COL_USE_MED     = 'Q37'

SUFFIX_SNAP     = '_1'
SUFFIX_WARBY    = '_2'
SUFFIX_MED      = '_3'

context_map = ['Social\n (SnapChat)', "Commercial\n (Warby Parker)", "Medical\n (PostureScreen)"]

COL_AUD_INTENTIONAL = 'Q59'
COL_AUD_BACKGROUND  = 'Q62'
COL_VIS_FACE_CORE   = 'Q73'
COL_VIS_PUPIL       = 'Q63'
COL_VIS_BKGD_OTHERS = 'Q64'
COL_VIS_BKGD_ME     = 'Q75'
COL_VIS_FACE_ALG    = 'Q65'
COL_VIS_NN_INTENT   = 'Q66'
COL_VIS_NN_ACCIDENT = 'Q74'
COL_VIS_OBJ_MEDS    = 'Q67'
COL_VIS_OBJ_SEX     = 'Q68'
COL_VIS_OBJ_MESSY   = 'Q69'
COL_VIS_OBJ_LICENSE = 'Q72'
COL_LOCATION        = 'Q70'
COL_PAYMENT         = 'Q74.1'

COL_RANK_DATA = 'Q73x'
COL_RANK_APPS = 'Q92'

COL_DEMO_AGE        = 'Q1_28'
COL_DEMO_GENDER     = 'Q2'
COL_DEMO_COUNTRY    = 'Q3'
COL_DEMO_EDU        = 'Q111'
COL_DEMO_TECHIE     = 'Q5'


LABEL_AUD_INTENTIONAL = 'Intentional Audio'
LABEL_AUD_BACKGROUND  = 'Background Audio'
LABEL_VIS_FACE_CORE   = 'Face (for core functionality)'
LABEL_VIS_PUPIL       = 'Pupil Dialation (to assess excitement)'
LABEL_VIS_BKGD_OTHERS = 'Other Faces in the Background'
LABEL_VIS_BKGD_ME     = 'My Face in the Background of Someone Else'
LABEL_VIS_FACE_ALG    = 'Face (for Improving the App)'
LABEL_VIS_NN_INTENT   = 'Near-Nudity (Intentional)'
LABEL_VIS_NN_ACCIDENT = 'Near-Nudity (Accidental)'
LABEL_VIS_OBJ_MEDS    = 'Object in Background (Meds)'
LABEL_VIS_OBJ_SEX     = 'Object in Background (Sexual)'
LABEL_VIS_OBJ_MESSY   = 'Object in Background (Mess)'
LABEL_VIS_OBJ_LICENSE = 'Object in Background (ID)'
LABEL_LOCATION        = 'Location'
LABEL_PAYMENT         = 'Payment Information'

LABEL_RANK_DATA = 'Q73x'
LABEL_RANK_APPS = 'Q92'

LABEL_DEMO_AGE      = 'Age'
LABEL_DEMO_GENDER   = 'Gender'
LABEL_DEMO_COUNTRY  = 'Country'
LABEL_DEMO_EDU      = 'Education Level'
LABEL_DEMO_TECHIE   = 'Tech-Savviness'

label_of = {}
label_of[COL_AUD_INTENTIONAL]   = LABEL_AUD_INTENTIONAL
label_of[COL_AUD_BACKGROUND]    = LABEL_AUD_BACKGROUND

label_of[COL_VIS_FACE_CORE]     = LABEL_VIS_FACE_CORE
label_of[COL_VIS_PUPIL]         = LABEL_VIS_PUPIL
label_of[COL_VIS_BKGD_OTHERS]   = LABEL_VIS_BKGD_OTHERS
label_of[COL_VIS_BKGD_ME]       = LABEL_VIS_BKGD_ME
label_of[COL_VIS_FACE_ALG]      = LABEL_VIS_FACE_ALG
label_of[COL_VIS_NN_INTENT]     = LABEL_VIS_NN_INTENT
label_of[COL_VIS_NN_ACCIDENT]   = LABEL_VIS_NN_ACCIDENT
label_of[COL_VIS_OBJ_MEDS]      = LABEL_VIS_OBJ_MEDS
label_of[COL_VIS_OBJ_SEX]       = LABEL_VIS_OBJ_SEX
label_of[COL_VIS_OBJ_MESSY]     = LABEL_VIS_OBJ_MESSY
label_of[COL_VIS_OBJ_LICENSE]   = LABEL_VIS_OBJ_LICENSE

label_of[COL_LOCATION]          = LABEL_LOCATION
label_of[COL_PAYMENT]           = LABEL_PAYMENT

SOLO_ANALYSES = [COL_VIS_FACE_CORE, COL_AUD_INTENTIONAL, COL_AUD_BACKGROUND, COL_VIS_PUPIL, 
                COL_VIS_BKGD_OTHERS, COL_VIS_BKGD_ME, COL_VIS_FACE_ALG, COL_VIS_NN_INTENT, 
                COL_VIS_NN_ACCIDENT, COL_VIS_OBJ_MEDS, COL_VIS_OBJ_SEX, COL_VIS_OBJ_MESSY,
                COL_VIS_OBJ_LICENSE, COL_LOCATION, COL_PAYMENT]

CROSS_ANALYSIS = {}
CROSS_ANALYSIS['audio']         = [COL_AUD_INTENTIONAL,    COL_AUD_BACKGROUND]
CROSS_ANALYSIS['near-nudity']   = [COL_VIS_NN_INTENT,      COL_VIS_NN_ACCIDENT]
CROSS_ANALYSIS['obj']           = [COL_VIS_OBJ_MEDS, COL_VIS_OBJ_SEX, COL_VIS_OBJ_MESSY, COL_VIS_OBJ_LICENSE]
CROSS_ANALYSIS['visual']        = [COL_VIS_PUPIL, COL_VIS_BKGD_OTHERS, COL_VIS_BKGD_ME, COL_VIS_FACE_ALG, COL_VIS_NN_INTENT, 
                                    COL_VIS_NN_ACCIDENT, COL_VIS_OBJ_MEDS, COL_VIS_OBJ_SEX, COL_VIS_OBJ_MESSY,
                                    COL_VIS_OBJ_LICENSE]
CROSS_ANALYSIS['face']          = [COL_VIS_FACE_CORE, COL_VIS_FACE_ALG, COL_VIS_BKGD_ME, COL_VIS_BKGD_OTHERS]
CROSS_ANALYSIS['all']           = SOLO_ANALYSES


def create_dir(filename):
    try:
        os.mkdir(filename)
    except OSError as error:
        print("Export repositories already created")    

create_dir(FILENAME_OUTPUTS)
create_dir(FILENAME_PLOTS)
create_dir(FILENAME_ANOVAS)


df = pd.read_csv('finalsurveyresults.csv')
print("Pandas data imported from CSV")

# print(df)

#Get the set of uniqueids (no duplicates)
idSet = set()
for ind in df.index: #how to iterate through rows
    row = df.loc[ind]
    idSet.add(row['ResponseId'])
    
print("Number of participants: " + str(len(idSet)))
print()

ageList = []
for ind in df.index: #how to iterate through rows
   row = df.loc[ind]
   ageList.append(row[COL_DEMO_AGE])


genderList = []
for ind in df.index: #how to iterate through rows
   row = df.loc[ind]
   genderList.append(row[COL_DEMO_GENDER])

# print("Ages: ")
# for item in ageList:
#    print(item)

# print("Genders: ")
# for item in genderList:
#    print(item)

categorical_cols = []

def make_anova(df, cols, title, fn):
    print("\tMAKING ANOVA")

    SIGNIFICANCE_CUTOFF = .4
    anova_text = title + "\n"
    # print("ANOVA FOR ")
    # print(analysis_label)
    # print(df[analysis_label])

    df_col = df[cols]
    df_col = pd.melt(df)
    df_col['context'] = df_col.apply(lambda row: context_map[cols.index(row['variable'])], axis=1)

    # print(df_col)
    # df_col.columns == ['variable', 'value']
    
    # val_min = df_col['value'].get(df_col['value'].idxmin())
    # val_max = df_col['value'].get(df_col['value'].idxmax())
    # homogenous_data = (val_min == val_max)
    homogenous_data = False

    if not homogenous_data:
        aov = pg.anova(dv='value', between='context', data=df_col)
        aov.round(3)

        anova_text = anova_text + str(aov)
        aov.to_csv(FILENAME_ANOVAS + fn + '-anova.csv')

        p_val = aov['p-unc'][0]
        print("\t\t" + title)
        print("\t\t" + 'Across contexts:' + "->" + " p=" + str(p_val))

        # if p_chair < SIGNIFICANCE_CUTOFF:
        #     print("Chair position is significant for " + analysis_label + ": " + str(p_chair))
        #     # print(title)
        # if p_path_method < SIGNIFICANCE_CUTOFF:
        #     print("Pathing method is significant for " + analysis_label + ": " + str(p_path_method))
        #     # print(title)

        # anova_text = anova_text + "\n"
        # Verify that subjects is legit
        # print(df[subject_id])

        # posthocs = pg.pairwise_ttests(dv=analysis_label, within=COL_PATHING, between=COL_CHAIR,
        #                           subject=subject_id, data=df)
        # # pg.print_table(posthocs)
        # anova_text = anova_text + "\n" + str(posthocs)
        # posthocs.to_csv(FILENAME_ANOVAS + fn + 'posthocs.csv')
        # print()

    else:
        print("! Issue creating ANOVA for " + analysis_label)
        print("Verify that there are at least a few non-identical values recorded")
        anova_text = anova_text + "Column homogenous with value " + str(val_min)


    f = open(FILENAME_ANOVAS + fn + "-anova.txt", "w")
    f.write(anova_text)
    f.close()

def make_boxplot(df, cols, title, fn):
    graph_type = "boxplot"
    plt.figure()

    df_new = df[cols]
    df_newest = pd.melt(df_new)
    df_newest['context'] = df_newest.apply(lambda row: context_map[cols.index(row['variable'])], axis=1)

    print("\tMAKING BOXPLOT")
    # print(df.values)
    bx = sns.boxplot(x="context", y="value", data=df_newest)

    # plt.tight_layout()
    # title = al_title[analysis] + "\n" + al_y_range
    # bx = sns.boxplot(data=df, x=COL_PATHING, y=analysis, hue=COL_CHAIR, order=cat_order)
    # print("San check on data")
    # print(df[analysis])
    # print(df[analysis].columns)

    bx.set(xlabel='Context')
    bx.set(title=title, ylabel="Comfort level")
    # bx.set(xticks=['Social\n (SnapChat)', "Commercial\n (Warby Parker)", "Medical\n (PostureScreen)"])
    figure = bx.get_figure()    
    figure.savefig(FILENAME_PLOTS + fn + '.png', bbox_inches='tight')
    plt.close()

def make_stripplot(df, analysis, fn, title):
    if OUTPUT_GRAPH_STRIPPLOT:
            graph_type = "stripplot"
            plt.figure()
            # plt.tight_layout()
            bplot=sns.stripplot(y=analysis, x=COL_PATHING, 
                           data=df_goal, 
                           jitter=True, 
                           marker='o', 
                           alpha=0.8,
                           hue=COL_CHAIR, order=cat_order)
            bplot.set(xlabel='Pathing Method')
            bplot.set(ylim=al_y_range[analysis])
            bplot.set(title=al_title[analysis], ylabel=al_y_units[analysis])
            figure = bplot.get_figure()    
            figure.savefig(FILENAME_PLOTS + fn + graph_type + '.png', bbox_inches='tight')
            plt.close()

def make_cross_df(df, fn):
    df_total = None

    for c in cross:
        col = c
        title = label_of[col]
        cols = get_subcols(col)
        df_new = df[cols]
        df_new = pd.melt(df_new)

        df_new['question'] = pd.Series([label_of[col] for x in range(len(df_new.index))])
        df_new['context'] = df_new.apply(lambda row: context_map[cols.index(row['variable'])], axis=1)

        # df_new['context'] = pd.Series([col for x in cols.index(df_new['variable'])])

        if df_total is None:
            df_total = df_new
        else:
            df_total = df_total.append(df_new)


    # df_total['value'] = [mapping[item] for item in df_total['value']]
    return df_total

def make_boxplot_2way(df, title):
    graph_type = "boxplot"
    plt.figure()
    print("\tMAKING BOXPLOT - 2WAY")
    # print(df.values)
    # bx = sns.boxplot(x="variable", y="value", data=df)
    # sorted_index = df.median().sort_values().index
    # print(sorted_index)
    bx = sns.boxplot(data=df, x='question', y='value', hue='context') #, order=cat_order)

    n = len(pd.unique(df['question']))

    if n > 3:
        bx.set_xticklabels(bx.get_xticklabels(), rotation=90)
        


    plt.tight_layout()
    # title = al_title[analysis] + "\n" + al_y_range
    # bx = sns.boxplot(data=df, x=COL_PATHING, y=analysis, hue=COL_CHAIR, order=cat_order)
    # print("San check on data")
    # print(df[analysis])
    # print(df[analysis].columns)

    bx.set(xlabel='Data Type')
    bx.set(title=title, ylabel="Comfort level")
    # bx.set(xticks=['Social\n (SnapChat)', "Commercial\n (Warby Parker)", "Medical\n (PostureScreen)"])
    figure = bx.get_figure()    
    figure.savefig(FILENAME_PLOTS + title + '-cross.png')#, bbox_inches='tight')
    plt.close()

def make_anova_2way(df, title):
    print("\tMAKING ANOVA")

    SIGNIFICANCE_CUTOFF = .4
    anova_text = title + "\n"
    # print("ANOVA FOR ")
    # print(analysis_label)
    # print(df[analysis_label])

    # bx = sns.boxplot(data=df, x='question', y='value', hue='context')

    # print(df_col)
    # df_col.columns == ['variable', 'value']
    
    # val_min = df_col['value'].get(df_col['value'].idxmin())
    # val_max = df_col['value'].get(df_col['value'].idxmax())
    # homogenous_data = (val_min == val_max)
    homogenous_data = False

    if not homogenous_data:
        aov = pg.anova(dv='value', between=['question', 'context'], data=df)
        aov.round(3)

        anova_text = anova_text + str(aov)
        aov.to_csv(FILENAME_ANOVAS + fn + '-anova.csv')

        p_vals = aov['p-unc']

        # if p_chair < SIGNIFICANCE_CUTOFF:
        #     print("Chair position is significant for " + analysis_label + ": " + str(p_chair))
        #     # print(title)
        # if p_path_method < SIGNIFICANCE_CUTOFF:
        #     print("Pathing method is significant for " + analysis_label + ": " + str(p_path_method))
        #     # print(title)

        # anova_text = anova_text + "\n"
        # Verify that subjects is legit
        # print(df[subject_id])

        # posthocs = pg.pairwise_ttests(dv=analysis_label, within=COL_PATHING, between=COL_CHAIR,
        #                           subject=subject_id, data=df)
        # # pg.print_table(posthocs)
        # anova_text = anova_text + "\n" + str(posthocs)
        # posthocs.to_csv(FILENAME_ANOVAS + fn + 'posthocs.csv')
        # print()

    else:
        print("! Issue creating ANOVA for " + analysis_label)
        print("Verify that there are at least a few non-identical values recorded")
        anova_text = anova_text + "Column homogenous with value " + str(val_min)


    f = open(FILENAME_ANOVAS + fn + "-anova.txt", "w")
    f.write(anova_text)
    f.close()

def get_subcols(col):
    vals = col.split(".")
    col = vals[0]
    suffix = ''
    if len(vals) > 1:
        suffix = '.' + vals[1]

    cols = [col + SUFFIX_SNAP + suffix, col + SUFFIX_WARBY + suffix, col + SUFFIX_MED + suffix]

    return cols

# drop text label row
df = df.drop(1)
# drop header row
df = df.drop(0)
print(df.columns)

sus = [COL_VIS_NN_ACCIDENT, COL_VIS_OBJ_SEX, COL_VIS_OBJ_LICENSE]

for col in SOLO_ANALYSES:
    print(col)
    label = label_of[col]
    fn = col
    cols = get_subcols(col)

    # Make results numeric for future use
    for col in cols:
        # print(col + " being mapped to ints")
        df[col] = [mapping[item] for item in df[col]]

    df_cols = df[cols]

    make_anova(df_cols, cols, label, fn)
    make_boxplot(df_cols, cols, label, fn)
    

    if col in sus:
        # print(df_cols)
        pass

print("\n~~~Making 2-way comparisons~~~")
for key in CROSS_ANALYSIS.keys():
    cross = CROSS_ANALYSIS[key]
    fn = key
    df_cross = make_cross_df(df, cross)

    print(key)
    make_boxplot_2way(df_cross, fn)
    make_anova_2way(df_cross, fn)


print("TODO")

# Sort the categories by mean in boxplot
# 2way anova and output
# Display contexts better than with key
# Bigger graph area overall
# Y-labels pretty


print("FINISHED")





