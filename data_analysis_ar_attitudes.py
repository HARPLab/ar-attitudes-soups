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
context_map_short = ["Social", "Commercial", "Medical"]
context_map_colors = ["Blues", "YlOrBr", "BuGn"]



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
LABEL_VIS_FACE_CORE   = 'My Face\n (for core functionality)'
LABEL_VIS_PUPIL       = 'Pupil Dialation\n (to assess excitement)'
LABEL_VIS_BKGD_OTHERS = 'Other Faces\n in the Background'
LABEL_VIS_BKGD_ME     = 'My Face\n in the Background of Someone Else'
LABEL_VIS_FACE_ALG    = 'My Face\n (for Improving the App)'
LABEL_VIS_NN_INTENT   = 'Near-Nudity\n (Intentional)'
LABEL_VIS_NN_ACCIDENT = 'Near-Nudity\n (Accidental)'
LABEL_VIS_OBJ_MEDS    = 'Object \n (Meds)'
LABEL_VIS_OBJ_SEX     = 'Object \n (Sexual)'
LABEL_VIS_OBJ_MESSY   = 'Object \n (Mess)'
LABEL_VIS_OBJ_LICENSE = 'Object \n (License)'
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

CROSS_TITLE = {}
CROSS_TITLE['audio']        = "Audio Datatypes"
CROSS_TITLE['near-nudity']  = "Near-Nudity Data"
CROSS_TITLE['obj']          = "Object Datatypes"
CROSS_TITLE['visual']       = "Visual Datatypes" 
CROSS_TITLE['face']         = "Face Datatypes"
CROSS_TITLE['all']          = "All Datatypes"



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

def make_anova_context(df, cols, title, fn, cid):
    print("\tMAKING ANOVA")

    fn = fn + "-" + str(cid)
    title_label = CROSS_TITLE[title]

    SIGNIFICANCE_CUTOFF = .4
    anova_text = title + "\n"
    # print("ANOVA FOR ")
    # print(analysis_label)
    # print(df[analysis_label])


    # print(df_col)
    # df_col.columns == ['variable', 'value']
    
    # val_min = df_col['value'].get(df_col['value'].idxmin())
    # val_max = df_col['value'].get(df_col['value'].idxmax())
    # homogenous_data = (val_min == val_max)
    homogenous_data = False

    # bx = sns.boxplot(x="value", y="question", data=df, palette=custom_palette)

    if not homogenous_data:
        aov = pg.anova(dv='value', between='question', data=df) #, subject='ResponseId')
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

        posthocs = df.pairwise_tukey(dv='value', between='question').round(3)
        # pg.print_table(posthocs)
        anova_text = anova_text + "\n" + str(posthocs)
        posthocs.to_csv(FILENAME_ANOVAS + fn + '-posthocs.csv')


    else:
        print("! Issue creating ANOVA for " + analysis_label)
        print("Verify that there are at least a few non-identical values recorded")
        anova_text = anova_text + "Column homogenous with value " + str(val_min)


    f = open(FILENAME_ANOVAS + fn + "-anova.txt", "w")
    f.write(anova_text)
    f.close()

def make_anova(df, cols, title, fn):
    print("\tMAKING ANOVA")

    SIGNIFICANCE_CUTOFF = .4
    anova_text = title + "\n"
    # print("ANOVA FOR ")
    # print(analysis_label)
    # print(df[analysis_label])

    slice_cols = cols
    slice_cols.append('ResponseId')

    df_col = df[slice_cols]
    df_col = pd.melt(df_col, id_vars='ResponseId')

    df_col['context'] = df_col.apply(lambda row: context_map[slice_cols.index(row['variable'])], axis=1)

    # print(df_col)
    # df_col.columns == ['variable', 'value']
    
    # val_min = df_col['value'].get(df_col['value'].idxmin())
    # val_max = df_col['value'].get(df_col['value'].idxmax())
    # homogenous_data = (val_min == val_max)
    homogenous_data = False

    if not homogenous_data:
        aov = pg.anova(dv='value', between='context', data=df_col) #, subject='ResponseId')
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

def make_boxplot_context(df, cols, title, fn, cid):
    fn = fn + "-" + str(cid)
    title_label = CROSS_TITLE[title]

    graph_type = "boxplot"
    plt.figure()

    fig_dims = (8, 7)
    fig, ax = plt.subplots(figsize=fig_dims)

    n = len(pd.unique(df['question']))
    custom_palette = sns.color_palette(context_map_colors[cid], n)
    # custom_palette = sns.color_palette("viridis", n)

    print("\tMAKING BOXPLOT")
    # cols = ['ResponseId', 'variable', 'value', 'question', 'context']
   
    bx = sns.boxplot(x="value", y="question", data=df, palette=custom_palette)

    # if n > 4:
    #     bx.set_xticklabels(bx.get_xticklabels(), rotation=90)

    # plt.tight_layout()
    # title = al_title[analysis] + "\n" + al_y_range
    # bx = sns.boxplot(data=df, x=COL_PATHING, y=analysis, hue=COL_CHAIR, order=cat_order)
    # print("San check on data")
    # print(df[analysis])
    # print(df[analysis].columns)

    bx.set(ylabel='Data Type')
    bx.set(title=title_label + " for " + context_map_short[cid])
    bx.set(xlabel="Comfort level")
    bx.set(xticklabels=['', '-2', '', '-1', '', '0', '', '1', '', '2'])
    # bx.set(xticks=['Social\n (SnapChat)', "Commercial\n (Warby Parker)", "Medical\n (PostureScreen)"])
    figure = bx.get_figure()    
    figure.savefig(FILENAME_PLOTS + fn + '.png', bbox_inches='tight')
    plt.close()


def make_boxplot(df, cols, title, fn):
    graph_type = "boxplot"
    plt.figure()

    custom_palette = sns.color_palette("colorblind", 3)
    # custom_palette = sns.color_palette("viridis", 3)

    df_new = df[cols]
    slice_cols = cols
    slice_cols.append('ResponseId')
    df_newest = pd.melt(df_new, id_vars="ResponseId")
    df_newest['context'] = df_newest.apply(lambda row: context_map[slice_cols.index(row['variable'])], axis=1)

    print("\tMAKING BOXPLOT")
    # print(df.values)
    bx = sns.boxplot(x="context", y="value", data=df_newest, palette=custom_palette)

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

        slice_cols = cols
        slice_cols.append('ResponseId')
        df_new = df[slice_cols]
        df_new = pd.melt(df_new, id_vars='ResponseId')

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
    print("\tMAKING BOXPLOT - 2WAY")

    fig_dims = (8, 5)
    fig, ax = plt.subplots(figsize=fig_dims)

    n = len(pd.unique(df['question']))   
    # print(n)

    custom_palette = sns.color_palette("colorblind", 3*n)
    # custom_palette = sns.color_palette("viridis", 3*n)
    # sns.palplot(custom_palette)

    # print(df.values)
    # bx = sns.boxplot(x="variable", y="value", data=df)
    # sorted_index = df.median().sort_values().index
    # print(sorted_index)
    bx = sns.boxplot(data=df, x='value', y='question', hue='context', palette=custom_palette) #, order=cat_order)

    # bx.tick_params('both', labelsize='15')
    # plt.legend(legend)
    # title = al_title[analysis] + "\n" + al_y_range
    # bx = sns.boxplot(data=df, x=COL_PATHING, y=analysis, hue=COL_CHAIR, order=cat_order)
    # print("San check on data")
    # print(df[analysis])
    # print(df[analysis].columns)

    handles, _ = bx.get_legend_handles_labels()   # Get the artists.
    bx.legend(handles, context_map) #, loc="top") # Associate manually the artists to a label.

    title_label = CROSS_TITLE[title]

    bx.set(xlabel='Comfort Level')
    # bx.set(xticklabels=['', '-2', '', '-1', '', '0', '', '1', '', '2'])
    bx.set(xticklabels=['', '-2', '-1', '0', '1', '2'])


    # bx.set(xticklabels=['', 'Extremely uncomfortable', '', 'Somewhat uncomfortable', '', 'Neutral', '', 'Somewhat comfortable', '', 'Extremely comfortable'])
    bx.set(title=title_label, ylabel="Data Type")
    plt.legend(bbox_to_anchor=(1.01, 1), borderaxespad=0)
    # plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    # bx.set(xticks=['Social\n (SnapChat)', "Commercial\n (Warby Parker)", "Medical\n (PostureScreen)"])
    figure = bx.get_figure()    
    if n > 4:
        bx.set_xticklabels(bx.get_xticklabels(), rotation=90)

    # figure.autofmt_xdate() 
    plt.tight_layout()
    figure.savefig(FILENAME_PLOTS + "cross-" + title + '.png')#, bbox_inches='tight')
    plt.close()

    counter = 0
    for context, df_context in df.groupby('context'):
        # print(df_context)
        print(len(df_context))
        context_id = counter
        counter += 1


        make_anova_context(df_context, cols, title, fn, context_id)
        make_boxplot_context(df_context, cols, title, fn, context_id)




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
        aov = pg.rm_anova(dv='value', within=['question', 'context'], subject='ResponseId', data=df)
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

        posthocs = pg.pairwise_ttests(dv='value', within=['question', 'context'], subject='ResponseId', data=df)
        # pg.print_table(posthocs)
        anova_text = anova_text + "\n" + str(posthocs)
        posthocs.to_csv(FILENAME_ANOVAS + fn + '-posthocs.csv')
        print()

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

    make_anova(df, cols, label, fn)
    make_boxplot(df, cols, label, fn)
    

    if col in sus:
        # print(df_cols)
        pass

# for col in CONTEXTS:
#     print(col)
#     label = label_of[col]
#     fn = col
#     cols = get_subcols(col)

#     # Make results numeric for future use
#     for col in cols:
#         # print(col + " being mapped to ints")
#         df[col] = [mapping[item] for item in df[col]]


    


print("\n~~~Making 2-way comparisons~~~")
for key in CROSS_ANALYSIS.keys():
    cross = CROSS_ANALYSIS[key]
    fn = key
    df_cross = make_cross_df(df, cross)

    print(key)
    make_boxplot_2way(df_cross, fn)
    make_anova_2way(df_cross, fn)


# print("TODO")

# Sort the categories by mean in boxplot
# 2way anova and output
# Display contexts better than with key
# Bigger graph area overall
# Y-labels pretty
# We  compare  the  reported  ranking  of  the  differentmodes in each condition with the Bradley-Terry model
# ranked choice analysis

print("FINISHED")





