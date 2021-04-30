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
COL_PAYMENT         = 'Q74'

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

D_VIS_FACE_CORE     = (COL_VIS_FACE_CORE,   LABEL_VIS_FACE_CORE)
D_AUD_INTENTIONAL   = (COL_AUD_INTENTIONAL, LABEL_AUD_INTENTIONAL)
D_AUD_BACKGROUND    = (COL_AUD_BACKGROUND,  LABEL_AUD_BACKGROUND)
D_VIS_PUPIL         = (COL_VIS_PUPIL,       LABEL_VIS_PUPIL)
D_VIS_BKGD_OTHERS   = (COL_VIS_BKGD_OTHERS,   LABEL_VIS_BKGD_OTHERS)
D_VIS_BKGD_ME       = (COL_VIS_BKGD_ME,       LABEL_VIS_BKGD_ME)
D_VIS_FACE_ALG      = (COL_VIS_FACE_ALG,      LABEL_VIS_FACE_ALG)
D_VIS_NN_INTENT     = (COL_VIS_NN_INTENT,     LABEL_VIS_NN_INTENT)
D_VIS_NN_ACCIDENT   = (COL_VIS_NN_ACCIDENT,   LABEL_VIS_NN_ACCIDENT)
D_VIS_OBJ_MEDS      = (COL_VIS_OBJ_MEDS,      LABEL_VIS_OBJ_MEDS)
D_VIS_OBJ_SEX       = (COL_VIS_OBJ_SEX,       LABEL_VIS_OBJ_SEX)
D_VIS_OBJ_MESSY     = (COL_VIS_OBJ_MESSY,     LABEL_VIS_OBJ_MESSY)
D_VIS_OBJ_LICENSE   = (COL_VIS_OBJ_LICENSE,   LABEL_VIS_OBJ_LICENSE)
D_LOCATION          = (COL_LOCATION,          LABEL_LOCATION)
D_PAYMENT           = (COL_PAYMENT,           LABEL_PAYMENT)


SOLO_ANALYSES = [D_VIS_FACE_CORE, D_AUD_INTENTIONAL, D_AUD_BACKGROUND, D_VIS_PUPIL, 
                D_VIS_BKGD_OTHERS, D_VIS_BKGD_OTHERS, D_VIS_FACE_ALG, D_VIS_NN_INTENT, 
                D_VIS_NN_ACCIDENT, D_VIS_OBJ_MEDS, D_VIS_OBJ_SEX, D_VIS_OBJ_MESSY,
                D_VIS_OBJ_LICENSE, D_LOCATION, D_PAYMENT]

CROSS_ANALYSIS = []
CROSS_ANALYSIS.append([D_AUD_INTENTIONAL,    D_AUD_BACKGROUND])
CROSS_ANALYSIS.append([D_VIS_NN_INTENT,      D_VIS_NN_ACCIDENT])
CROSS_ANALYSIS.append([D_VIS_OBJ_MEDS, D_VIS_OBJ_SEX, D_VIS_OBJ_MESSY, D_VIS_OBJ_LICENSE])


def create_dir(filename):
    try:
        os.mkdir(filename)
    except OSError as error:
        print("Export repositories already created")    

if FLAG_EXPORT:
    create_dir(FILENAME_OUTPUTS)
    create_dir(FILENAME_PLOTS)
    create_dir(FILENAME_ANOVAS)


df = pd.read_csv('finalsurveyresults.csv')
print("Pandas data imported from CSV")

print(df)

#Get the set of uniqueids (no duplicates)
idSet = set()
for ind in df.index: #how to iterate through rows
    row = df.loc[ind]
    idSet.add(row['ResponseId'])
    
print("Number of participants: " + str(len(idSet)))
print("participants: "+ str(idSet))

ageList = []
for ind in df.index: #how to iterate through rows
   row = df.loc[ind]
   ageList.append(row[COL_DEMO_AGE])


genderList = []
for ind in df.index: #how to iterate through rows
   row = df.loc[ind]
   genderList.append(row[COL_DEMO_GENDER])

print("Ages: ")
for item in ageList:
   print(item)

print("Genders: ")
for item in genderList:
   print(item)



def analyze_all_participants(df):
    print(df.shape)
    
    df.loc[:, df.dtypes == 'float64']   = df.loc[:, df.dtypes == 'float64'].astype('float')
    df.loc[:, df.dtypes == 'int64']     = df.loc[:, df.dtypes == 'int64'].astype('int')

    print("Time to make some graphs \n")
    return df


def make_anova(df, analysis_label, fn, title):
    SIGNIFICANCE_CUTOFF = .4
    if OUTPUT_CALC_ANOVA:
        anova_text = title + "\n"
        # print("ANOVA FOR ")
        # print(analysis_label)
        # print(df[analysis_label])

        subject_id = 'uniqueid'

        df_col = df[analysis_label]
        val_min = df_col.get(df_col.idxmin())
        val_max = df_col.get(df_col.idxmax())
        homogenous_data = (val_min == val_max)

        if not homogenous_data:
            print("~~~ ANALYSIS FOR " + analysis_label + " ~~~")
            aov = pg.mixed_anova(dv=analysis_label, between=COL_CHAIR, within=COL_PATHING, subject=subject_id, data=df)
            aov.round(3)

            anova_text = anova_text + str(aov)
            aov.to_csv(FILENAME_ANOVAS + fn + 'anova.csv')

            p_vals = aov['p-unc']
            p_chair = p_vals[0]
            p_path_method = p_vals[1]

            if p_chair < SIGNIFICANCE_CUTOFF:
                print("Chair position is significant for " + analysis_label + ": " + str(p_chair))
                # print(title)
            if p_path_method < SIGNIFICANCE_CUTOFF:
                print("Pathing method is significant for " + analysis_label + ": " + str(p_path_method))
                # print(title)

            anova_text = anova_text + "\n"
            # Verify that subjects is legit
            # print(df[subject_id])

            posthocs = pg.pairwise_ttests(dv=analysis_label, within=COL_PATHING, between=COL_CHAIR,
                                      subject=subject_id, data=df)
            # pg.print_table(posthocs)
            anova_text = anova_text + "\n" + str(posthocs)
            posthocs.to_csv(FILENAME_ANOVAS + fn + 'posthocs.csv')
            print()

        else:
            print("! Issue creating ANOVA for " + analysis_label)
            print("Verify that there are at least a few non-identical values recorded")
            anova_text = anova_text + "Column homogenous with value " + str(val_min)


        f = open(FILENAME_ANOVAS + fn + "anova.txt", "w")
        f.write(anova_text)
        f.close()

def make_boxplot(df, analysis, fn, title):
    if OUTPUT_GRAPH_BOXPLOT:
        graph_type = "boxplot"
        plt.figure()
        # plt.tight_layout()
        # title = al_title[analysis] + "\n" + al_y_range
        bx = sns.boxplot(data=df, x=COL_PATHING, y=analysis, hue=COL_CHAIR, order=cat_order)
        # print("San check on data")
        # print(df[analysis])
        # print(df[analysis].columns)

        bx.set(xlabel='Pathing Method')
        ylims = al_y_range[analysis]
        bx.set(ylim=ylims)
        bx.set(title=title, ylabel=al_y_units[analysis])
        figure = bx.get_figure()    
        figure.savefig(FILENAME_PLOTS + fn + graph_type + '.png', bbox_inches='tight')
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

def inspect_troublemakers(df_analyzed, list_of_lookup_packets):
    # print(df_analyzed[P_LOOKUP])

    for t in list_of_lookup_packets:
        df_trouble = df_analyzed[df_analyzed[P_LOOKUP] == t]
        df_trouble = df_trouble.iloc[0]

        # Should only be one
        t_id = t
        t_id = t_id.replace("(", "")
        t_id = t_id.replace(")", "")
        t_id = t_id.replace("\'", "")
        t_id = t_id.replace(", ", "-")
        print("Found and generating raw slider log for " + t_id)

        fn = "trouble-" + t_id + ".png"
        plot_analysis_one_participant(df_trouble, t, fn)
        # Add dirty data marker, too


'''
 END: METHOD DECLARATIONS
'''


print("FINISHED")




