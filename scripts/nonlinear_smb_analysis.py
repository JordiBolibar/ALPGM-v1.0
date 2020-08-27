# -*- coding: utf-8 -*-
"""
Created on Sun Aug 23 13:13:41 2020

@author: bolibarj
"""

import os
#from itertools import cycle
#import seaborn as sns
#from scipy.spatial.distance import euclidean
import numpy.polynomial.polynomial as poly
import matplotlib.pyplot as plt
import proplot as plot
import copy
import numpy as np
#import seaborn as sns
import math
from numpy import genfromtxt
from pathlib import Path
import shutil
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.preprocessing import StandardScaler, normalize, MinMaxScaler
#from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.linear_model import LassoCV
import scipy.stats as st
import xarray as xr

from keras import backend as K
from keras.models import load_model

#from itertools import combinations 
from scipy.stats import gaussian_kde

workspace = Path(os.getcwd()).parent 
root = workspace.parent
path_smb = os.path.join(workspace, 'glacier_data', 'smb')
path_smb_function_validation = os.path.join(workspace, 'glacier_data', 'smb', 'smb_function', 'Lasso_validation')
path_smb_function = os.path.join(workspace, 'glacier_data', 'smb', 'smb_function')
#SMB_raw_o = genfromtxt(path_smb + 'SMB_raw_extended.csv', delimiter=';', dtype=float)
SMB_raw = genfromtxt(os.path.join(path_smb, 'SMB_raw_temporal.csv'), delimiter=';', dtype=float)
path_ann_LOGO = os.path.join(path_smb , 'ANN', 'LOGO')
path_ann_LOYO = os.path.join(path_smb, 'ANN', 'LOYO')
path_ann_LSYGO = os.path.join(path_smb, 'ANN', 'LSYGO')
path_ann_LSYGO_hard_2 = os.path.join(path_smb, 'ANN', 'LSYGO_hard')
path_ann_LSYGO_hard = "C:\\Users\\bolibarj\\Desktop\\ALPGM_backup\\LSYGO_hard"
#path_ann_LSYGO_hard = os.path.join(path_smb, 'ANN', 'LSYGO_future')
path_glims = os.path.join(workspace, 'glacier_data', 'GLIMS') 

path_ann = path_ann_LSYGO_hard
path_cv_ann = os.path.join(path_ann, 'CV')
path_ensemble_ann = os.path.join(path_ann, 'ensemble')
path_cv_lasso = os.path.join(path_smb, 'smb_function', 'Lasso_LSYGO_ensemble')

path_dataset = 'C:\\Jordi\\PhD\\Publications\\Second article\\Dataset\\'

########   MAIN   ########################

def r2_keras(y_true, y_pred):
    SS_res =  K.sum(K.square(y_true - y_pred)) 
    SS_tot = K.sum(K.square(y_true - K.mean(y_true))) 
    return ( 1 - SS_res/(SS_tot + K.epsilon()) )

def root_mean_squared_error(y_true, y_pred):
        return K.sqrt(K.mean(K.square(y_pred - y_true))) 
    
### Load full SMB and topo-climatic dataset

with open(os.path.join(root, 'X_nn_extended.txt'), 'rb') as x_f:
    X = np.load(x_f)
with open(os.path.join(root, 'y_extended.txt'), 'rb') as y_f:
    y_o = np.load(y_f)
    
with open(os.path.join(root, 'X_lasso.txt'), 'rb') as x_f:
    X_lasso = np.load(x_f)
    
with open(os.path.join(path_smb, 'x_reconstructions.txt'), 'rb') as x_f:
    x_reconstructions = np.load(x_f)
    
with open(os.path.join(path_smb, 'x_reconstructions_lasso.txt'), 'rb') as x_f:
    x_reconstructions_lasso = np.load(x_f)
    
### We filter the combinations of topo-climatic predictors from Lasso
pred_names = np.array(['CPDD', 'W snow', 'S snow', 'Zmean', 'Zmax', 'Slope', 'Area', 'Lon', 'Lat', 'Aspect', 'Temp M1', 'Temp M2', 'Temp M3', 'Temp M4', 'Temp M5', 'Temp M6', 'Temp M7', 'Temp M8', 'Temp M9', 'Temp M10', 'Temp M11', 'Temp M12', 'Snow1', 'Snow2', 'Snow3', 'Snow4', 'Snow5', 'Snow6', 'Snow7', 'Snow8', 'Snow9', 'Snow10', 'Snow11', 'Snow12'])
pred_names_MB = np.insert(pred_names, 0, 'SMB')

lasso_mask = np.array([True, True, True, True, True, True, True, True, True, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True])
X_lasso_truncated = X_lasso[:,lasso_mask]
    
### Load 1967-2015 Lasso and DL reconstructions
ds_smb_lasso_reconstructions = xr.open_dataset(os.path.join(path_dataset, 'lasso', 'french_alpine_glaciers_MB_reconstruction_1967_2015.nc'))
ds_smb_nn_reconstructions = xr.open_dataset(os.path.join(path_dataset, 'LSYGO', 'french_alpine_glaciers_MB_reconstruction_1967_2015.nc'))

glims_rabatel = genfromtxt(os.path.join(path_glims, 'GLIMS_Rabatel_30_2003.csv'), delimiter=';', skip_header=1,  dtype=[('Area', '<f8'), ('Perimeter', '<f8'), ('Glacier', '<a50'), ('Annee', '<i8'), ('Massif', '<a50'), ('MEAN_Pixel', '<f8'), ('MIN_Pixel', '<f8'), ('MAX_Pixel', '<f8'), ('MEDIAN_Pixel', '<f8'), ('Length', '<f8'), ('Aspect', '<a50'), ('x_coord', '<f8'), ('y_coord', '<f8'), ('slope20', '<f8'), ('GLIMS_ID', '<a50'), ('Massif_SAFRAN', '<f8'), ('Aspect_num', '<f8')])        
glims_2003 = genfromtxt(os.path.join(path_glims, 'GLIMS_2003.csv'), delimiter=';', skip_header=1,  dtype=[('Area', '<f8'), ('Perimeter', '<f8'), ('Glacier', '<a50'), ('Annee', '<i8'), ('Massif', '<a50'), ('MEAN_Pixel', '<f8'), ('MIN_Pixel', '<f8'), ('MAX_Pixel', '<f8'), ('MEDIAN_Pixel', '<f8'), ('Length', '<f8'), ('Aspect', '<a50'), ('x_coord', '<f8'), ('y_coord', '<f8'), ('GLIMS_ID', '<a50'), ('Massif_SAFRAN', '<i8'), ('Aspect_num', '<i8'), ('ID', '<f8')])

# Remove duplicated index to allow correct filtering
unique_idxs_lasso = np.unique(ds_smb_lasso_reconstructions.GLIMS_ID.values, return_index=True)[1:][0]
ds_smb_lasso_reconstructions = ds_smb_lasso_reconstructions.isel(GLIMS_ID = unique_idxs_lasso)
ds_smb_lasso_reconstructions = ds_smb_lasso_reconstructions.isel(RGI_ID = unique_idxs_lasso)
ds_smb_lasso_reconstructions = ds_smb_lasso_reconstructions.isel(name = unique_idxs_lasso)

unique_idxs_nn = np.unique(ds_smb_nn_reconstructions.GLIMS_ID.values, return_index=True)[1:][0]
ds_smb_nn_reconstructions = ds_smb_nn_reconstructions.isel(GLIMS_ID = unique_idxs_nn)
ds_smb_nn_reconstructions = ds_smb_nn_reconstructions.isel(RGI_ID = unique_idxs_nn)
ds_smb_nn_reconstructions = ds_smb_nn_reconstructions.isel(name = unique_idxs_nn)

# Rabatel glaciers
rabatel_idxs, rabatel_areas = [],[]
for glacier in glims_rabatel:
    idx = np.where(glacier['GLIMS_ID'].decode('UTF-8') == ds_smb_lasso_reconstructions.GLIMS_ID.values)[0][0]
    rabatel_idxs.append(idx)
    rabatel_areas.append(glacier['Area'])
rabatel_idxs = np.asarray(rabatel_idxs)
rabatel_areas = np.asarray(rabatel_areas)

rabatel_areas_flat = copy.deepcopy(rabatel_areas).reshape(1,-1)
for i in range(0,56):
    rabatel_areas_flat = np.concatenate((rabatel_areas_flat, rabatel_areas.reshape(1,-1)), axis=0)
    
rabatel_areas_flat = rabatel_areas_flat.flatten()
finite_mask = np.isfinite(y_o.flatten())
rabatel_areas_flat = rabatel_areas_flat[finite_mask]

rabatel_area_idx = np.where(rabatel_areas_flat < 0.5)

# Area filter
area_reconstructions = []
for ID in ds_smb_lasso_reconstructions.RGI_ID.values:
    if(ID != 0):
        idx = np.where(ID == glims_2003['ID'])[0][0]
        area_reconstructions.append(glims_2003['Area'][idx])
    else:
        area_reconstructions.append(np.nan)
area_reconstructions = np.asarray(area_reconstructions)

small_area_idx = np.where(area_reconstructions < 0.5)
large_area_idx = np.where(area_reconstructions > 0.5)

# Area filter
zmean_reconstructions = []
for ID in ds_smb_lasso_reconstructions.RGI_ID.values:
    if(ID != 0):
        idx = np.where(ID == glims_2003['ID'])[0][0]
        zmean_reconstructions.append(glims_2003['MEAN_Pixel'][idx])
    else:
        zmean_reconstructions.append(np.nan)
zmean_reconstructions = np.asarray(zmean_reconstructions)

high_zmean_idx = np.where(zmean_reconstructions > 3000)
low_zmean_idx = np.where(zmean_reconstructions < 3000)


#####

path_CV_ensemble = path_cv_ann
path_CV_ensemble_members = np.asarray(os.listdir(path_CV_ensemble))
#
path_CV_lasso_ensemble = path_cv_lasso
path_CV_lasso_ensemble_members = np.asarray(os.listdir(path_CV_lasso_ensemble))
path_ensemble_members = np.asarray(os.listdir(path_ensemble_ann))

CV_ensemble_members = np.ndarray(path_CV_ensemble_members.shape, dtype=np.object)
ensemble_members = np.ndarray(path_ensemble_members.shape, dtype=np.object)
CV_lasso_ensemble_members = np.ndarray(path_CV_lasso_ensemble_members.shape, dtype=np.object)

#member_idx = 0
#print("\nPreloading CV Lasso ensemble SMB models...")
#for path_CV_member in path_CV_lasso_ensemble_members:
#    # We retrieve the ensemble member ANN model
#    with open(os.path.join(path_CV_lasso_ensemble, path_CV_member), 'rb') as lasso_model_f:
#        lasso_CV_member_model = np.load(lasso_model_f,  allow_pickle=True)
#    
#    CV_lasso_ensemble_members[member_idx] = lasso_CV_member_model
#    print("|", end="", flush=True)
#    member_idx = member_idx+1

#member_idx = 0
#print("\nPreloading CV ensemble SMB models...")
#for path_CV_member in path_CV_ensemble_members:
#    # We retrieve the ensemble member ANN model
#    ann_CV_member_model = load_model(os.path.join(path_CV_ensemble, path_CV_member), custom_objects={"r2_keras": r2_keras, "root_mean_squared_error": root_mean_squared_error}, compile=False)
##        CV_ensemble_members.append(ann_CV_member_model)
#    CV_ensemble_members[member_idx] = ann_CV_member_model
#    print("|", end="", flush=True)
#    member_idx = member_idx+1

#member_idx = 0
#print("\n\nPreloading ensemble full SMB models...")
#for path_member in path_ensemble_members:
#    # We retrieve the ensemble member ANN model
#    ann_member_model = load_model(os.path.join(path_ensemble_ann, path_member, 'ann_glacier_model.h5'), custom_objects={"r2_keras": r2_keras, "root_mean_squared_error": root_mean_squared_error}, compile=False)
##        ensemble_members.append(ann_member_model)
#    ensemble_members[member_idx] = ann_member_model
#    print("|", end="", flush=True)
#    member_idx = member_idx+1

###### Ensemble simulations #####
SMB_lasso_members, SMB_nn_cv_members, SMB_nn_ensemble_members = [],[],[]

finite_mask = np.isfinite(y_o.flatten())
y = y_o.flatten()[finite_mask]

data_filter = y == y

years = copy.deepcopy(y_o)

for i in range(0,32):
    years[i,:] = range(1959,2016)

years = years.flatten()[finite_mask]

##### Massive extraction of all input predictors   ############

# Deep learning
pred_nn = {'pred':[], 'idx':[], 'bias':[], 'steps':[]}
for pred_idx in range(0, X[0,:].size):
    pred_nn['pred'].append(np.asarray(X[:,pred_idx][finite_mask]))
    pred_nn['idx'].append(pred_idx)
pred_nn['pred'] = np.asarray(pred_nn['pred'])
pred_nn['idx'] = np.asarray(pred_nn['idx'])

# Lasso
pred_lasso = {'pred':[], 'idx':[], 'bias':[], 'steps':[]}
for pred_idx in range(0, X_lasso_truncated[0,:].size):
    pred_lasso['pred'].append(np.asarray(X_lasso_truncated[:,pred_idx]))
    pred_lasso['idx'].append(pred_idx)
pred_lasso['pred'] = np.asarray(pred_lasso['pred'])
pred_lasso['idx'] = np.asarray(pred_lasso['idx'])

# Predictors from 1967-2015 reconstructions with DL
pred_rec = {'pred':[], 'idx':[], 'steps':[]}
for pred_idx in range(0, x_reconstructions[0,:].size):
    pred_rec['pred'].append(np.asarray(x_reconstructions[:,pred_idx]))
    pred_rec['idx'].append(pred_idx)
pred_rec['pred'] = np.asarray(pred_rec['pred'])
pred_rec['idx'] = np.asarray(pred_rec['idx'])

# Predictors from 1967-2015 reconstructions with Lasso
pred_rec_lasso = {'pred':[], 'idx':[], 'steps':[]}
for pred_idx in range(0, x_reconstructions_lasso[0,:].size):
    pred_rec_lasso['pred'].append(np.asarray(x_reconstructions_lasso[:,pred_idx]))
    pred_rec_lasso['idx'].append(pred_idx)
pred_rec_lasso['pred'] = np.asarray(pred_rec_lasso['pred'])
pred_rec_lasso['idx'] = np.asarray(pred_rec_lasso['idx'])

#### Filtering of predictors per two main types of behaviour  ######
# Area
small_area_filter = np.where(pred_rec['pred'][8,:].astype(float) < 0.5)[0]
large_area_filter = np.where(pred_rec['pred'][8,:].astype(float) >= 0.5)[0]

small_predictors = pred_rec['pred'][:,small_area_filter]
large_predictors = pred_rec['pred'][:,large_area_filter]

#Altitude
low_zmean_filter = np.where(pred_rec['pred'][5,:].astype(float) < 3000)[0]
high_zmean_filter = np.where(pred_rec['pred'][5,:].astype(float) >= 3000)[0]

high_zmean_predictors = pred_rec['pred'][:,low_zmean_filter]
low_zmean_predictors = pred_rec['pred'][:,high_zmean_filter]

# MB
# DL
ext_pos_MB_filter = np.where(pred_rec['pred'][1,:].astype(float) > 0.5)[0]
ext_neg_MB_filter = np.where(pred_rec['pred'][1,:].astype(float) < -2)[0]

ext_pos_MB_predictors = pred_rec['pred'][:,ext_pos_MB_filter]
ext_neg_MB_predictors = pred_rec['pred'][:,ext_neg_MB_filter]

# Lasso
ext_pos_MB_filter_lasso = np.where(pred_rec_lasso['pred'][1,:].astype(float) > 0.5)[0]
ext_neg_MB_filter_lasso = np.where(pred_rec_lasso['pred'][1,:].astype(float) < -2)[0]

ext_pos_MB_predictors_lasso = pred_rec_lasso['pred'][:,ext_pos_MB_filter_lasso]
ext_neg_MB_predictors_lasso = pred_rec_lasso['pred'][:,ext_neg_MB_filter_lasso]

#import pdb; pdb.set_trace()

#import pdb; pdb.set_trace()

################################

area_nn = X[:,6][finite_mask][data_filter] 
area_lasso = X_lasso[:,6][data_filter] 

slope_nn = X[:,5][finite_mask][data_filter] 
slope_lasso = X_lasso[:,5][data_filter] 

cpdd_nn = X[:,0][finite_mask][data_filter] 
cpdd_lasso = X_lasso[:,0][data_filter] 

wsnow_nn = X[:,1][finite_mask][data_filter] 
wsnow_lasso = X_lasso[:,1][data_filter] 

ssnow_nn = X[:,2][finite_mask][data_filter] 
ssnow_lasso = X_lasso[:,2][data_filter] 

X = X[finite_mask,:]

with open(os.path.join(path_smb_function, 'model_lasso_spatial.txt'), 'rb') as lasso_model_f:
    lasso_single_model = np.load(lasso_model_f,  allow_pickle=True)

### Perform ensemble simulations  ###############
#for lasso_model in CV_lasso_ensemble_members[:-2]:
#    SMB_lasso_member = lasso_model[()].predict(X_lasso)
#    SMB_lasso_members.append(SMB_lasso_member)
    
#for nn_model in CV_ensemble_members:
##    import pdb; pdb.set_trace()
#    SMB_nn_member = nn_model.predict(X, batch_size=34).flatten()
#    SMB_nn_cv_members.append(SMB_nn_member)
#    
#for nn_model in ensemble_members:
##    import pdb; pdb.set_trace()
#    SMB_nn_member = nn_model.predict(X, batch_size=34).flatten()
#    SMB_nn_ensemble_members.append(SMB_nn_member)
#
SMB_lasso_members = np.asarray(SMB_lasso_members)
SMB_nn_cv_members = np.asarray(SMB_nn_cv_members)
SMB_nn_ensemble_members = np.asarray(SMB_nn_ensemble_members)

# Save simulations by Lasso ensemble
#with open(os.path.join(path_smb_function_validation, 'SMB_lasso_members.txt'), 'wb') as lasso_f:
#    np.save(lasso_f, SMB_lasso_members)
## Save simulations by deep learning ensemble
#with open(os.path.join(path_smb_function_validation, 'SMB_nn_cv_members.txt'), 'wb') as nn_f:
#    np.save(nn_f, SMB_nn_cv_members)
#with open(os.path.join(path_smb_function_validation, 'SMB_nn_ensemble_members.txt'), 'wb') as nn_f:
#    np.save(nn_f, SMB_nn_ensemble_members)
    
## Load ensemble simulations  
with open(os.path.join(path_smb_function_validation, 'SMB_lasso_members.txt'), 'rb') as lasso_f:
    SMB_lasso_members = np.load(lasso_f)
with open(os.path.join(path_smb_function_validation, 'SMB_nn_cv_members.txt'), 'rb') as nn_f:
    SMB_nn_cv_members = np.load(nn_f)
with open(os.path.join(path_smb_function_validation, 'SMB_nn_ensemble_members.txt'), 'rb') as nn_f:
    SMB_nn_ensemble_members = np.load(nn_f)
    
# Model results during cross-validation in glacier_neural_network_keras.py
    
with open(os.path.join(path_cv_lasso, 'SMB_lasso_all.txt'), 'rb') as lasso_f:
    SMB_lasso_all_CV = np.load(lasso_f)
with open(os.path.join(path_cv_lasso, 'SMB_lasso_obs_all.txt'), 'rb') as lasso_f:
    SMB_lasso_obs_CV = np.load(lasso_f)
with open(os.path.join(path_ann_LSYGO_hard_2, 'SMB_nn_all.txt'), 'rb') as nn_f:
    SMB_nn_all_CV = np.load(nn_f)
with open(os.path.join(path_ann_LSYGO_hard_2, 'SMB_nn_obs_all.txt'), 'rb') as nn_f:
    SMB_nn_obs_CV = np.load(nn_f)
    
    
y = y[data_filter]    
    
lasso_prediction = np.mean(SMB_lasso_members, axis=0)[data_filter]
#lasso_prediction = SMB_lasso_members[-1]
    
lasso_prediction_single = lasso_single_model.predict(X_lasso)[data_filter]
    
nn_cv_prediction = np.mean(SMB_nn_cv_members, axis=0)[data_filter]
nn_ensemble_prediction = np.mean(SMB_nn_ensemble_members, axis=0)[data_filter]
#nn_ensemble_prediction = SMB_nn_ensemble_members[10][data_filter]

nn_prediction = nn_cv_prediction

bias_lasso = lasso_prediction - y
bias_nn_cv = nn_cv_prediction - y
bias_nn_ensemble = nn_ensemble_prediction - y

bias_lasso_area = bias_lasso
bias_nn_area = bias_nn_ensemble

bias_nn = bias_nn_cv

years = years[data_filter]

print("\nLasso ensemble RMSE: " + str(math.sqrt(mean_squared_error(y, lasso_prediction))))
print("\nLasso single RMSE: " + str(math.sqrt(mean_squared_error(y, lasso_prediction_single))))
#print("\nDeep learning CV RMSE: " + str(math.sqrt(mean_squared_error(y, nn_cv_prediction))))
print("\nDeep learning ensemble RMSE: " + str(math.sqrt(mean_squared_error(y, nn_ensemble_prediction))))
print("\n-------------------")

print("\nObs mean value: " + str(y.mean()))
print("\nLasso ensemble mean value: " + str(lasso_prediction.mean()))
print("\nLasso single mean value: " + str(lasso_prediction_single.mean()))
#print("\nNN CV mean value: " + str(nn_cv_prediction.mean()))
print("\nNN ensemble mean value: " + str(nn_ensemble_prediction.mean()))

print("\n-------------------")
print("\nLasso mean bias: " + str(bias_lasso.mean()))
#print("\nNN CV mean bias: " + str(bias_nn_cv.mean()))
print("\nNN ensemble mean bias: " + str(bias_nn_ensemble.mean()))

####################################################
######## Bias computation per predictor  ############
#####################################################

##### Massive computation  ##############
#import pdb; pdb.set_trace()

###### Deep learning  #####
# Loop through predictors
for predictor in pred_nn['pred']:
    step = (predictor.max() - predictor.min())/10
    pred_nn['steps'].append(step)
#    print("predictor: " + str(predictor))
#    print("step: " + str(step))
    # Loop through steps
    biases = []
    for value in np.arange(predictor.min(), predictor.max(), step):
#        print("value: " + str(value))
        value_idx = np.where((predictor < (value + step)) & (predictor > value))
        biases.append(np.mean(bias_nn[value_idx]))
    pred_nn['bias'].append(np.asarray(biases))
        
pred_nn['bias'] = np.asarray(pred_nn['bias'])     
pred_nn['steps'] = np.asarray(pred_nn['steps'])   

###### Lasso  ####
# Loop through predictors
for predictor in pred_lasso['pred']:
    step = (predictor.max() - predictor.min())/10
    pred_lasso['steps'].append(step)
    # Loop through steps
    biases = []
    for value in np.arange(predictor.min(), predictor.max(), step):
        value_idx = np.where((predictor < (value + step)) & (predictor > value))
        biases.append(np.mean(bias_lasso[value_idx]))
    pred_lasso['bias'].append(np.asarray(biases))
        
pred_lasso['bias'] = np.asarray(pred_lasso['bias'])     
pred_lasso['steps'] = np.asarray(pred_lasso['steps'])  

#import pdb; pdb.set_trace()

#### Manual computation  ####################################################

# Bias per year
lasso_bias_per_year, nn_bias_per_year = [],[]
for year in range(1959,2016):
    year_idx = np.where(years == year)
    lasso_bias_per_year.append(np.mean(bias_lasso[year_idx]))
    nn_bias_per_year.append(np.mean(bias_nn[year_idx]))
lasso_bias_per_year = np.asarray(lasso_bias_per_year)
nn_bias_per_year = np.asarray(nn_bias_per_year)

# Bias per glacier area size
lasso_bias_per_area, nn_bias_per_area = [],[]
for area in np.arange(0,33, 0.25):
#    import pdb; pdb.set_trace()
    area_lasso_idx = np.where((area_lasso < (area + 0.25)) & (area_lasso > area))
    lasso_bias_per_area.append(np.mean(bias_lasso[area_lasso_idx]))
    
    area_nn_idx = np.where((area_nn < (area + 0.25)) & (area_nn > area))
    nn_bias_per_area.append(np.mean(bias_nn[area_nn_idx]))
    
lasso_bias_per_area = np.asarray(lasso_bias_per_area)
nn_bias_per_area = np.asarray(nn_bias_per_area)

# Bias per glacier slope
lasso_bias_per_slope, nn_bias_per_slope = [],[]
for slope in np.arange(0,50, 2):
#    import pdb; pdb.set_trace()
    slope_lasso_idx = np.where((slope_lasso < (slope + 2)) & (slope_lasso > slope))
    lasso_bias_per_slope.append(np.mean(bias_lasso[slope_lasso_idx]))
    
    slope_nn_idx = np.where((slope_nn < (slope + 2)) & (slope_nn > slope))
    nn_bias_per_slope.append(np.mean(bias_nn[slope_nn_idx]))
    
lasso_bias_per_slope = np.asarray(lasso_bias_per_slope)
nn_bias_per_slope = np.asarray(nn_bias_per_slope)

# Bias per glacier MB
lasso_bias_per_MB, nn_bias_per_MB = [],[]
for MB in np.arange(-5,5, 0.5):
#    import pdb; pdb.set_trace()
    MB_lasso_idx = np.where((y < (MB + 0.5)) & (y > MB))
    lasso_bias_per_MB.append(np.mean(bias_lasso[MB_lasso_idx]))
    
    MB_nn_idx = np.where((y < (MB + 0.5)) & (y > MB))
    nn_bias_per_MB.append(np.mean(bias_nn[MB_nn_idx]))
    
lasso_bias_per_MB = np.asarray(lasso_bias_per_MB)
nn_bias_per_MB = np.asarray(nn_bias_per_MB)

# Bias per glacier CPDD
lasso_bias_per_cpdd, nn_bias_per_cpdd = [],[]
for cpdd in np.arange(-1000, 1000, 100):
#    import pdb; pdb.set_trace()
    cpdd_lasso_idx = np.where((cpdd_lasso < (cpdd + 100)) & (cpdd_lasso > cpdd))
    lasso_bias_per_cpdd.append(np.mean(bias_lasso[cpdd_lasso_idx]))
    
    cpdd_nn_idx = np.where((cpdd_nn < (cpdd + 100)) & (cpdd_nn > cpdd))
    nn_bias_per_cpdd.append(np.mean(bias_nn[cpdd_nn_idx]))
    
lasso_bias_per_cpdd = np.asarray(lasso_bias_per_cpdd)
nn_bias_per_cpdd = np.asarray(nn_bias_per_cpdd)

# Bias per glacier winter snow
lasso_bias_per_wsnow, nn_bias_per_wsnow = [],[]
for wsnow in np.arange(-1500, 1500, 100):
#    import pdb; pdb.set_trace()
    wsnow_lasso_idx = np.where((wsnow_lasso < (wsnow + 100)) & (wsnow_lasso > wsnow))
    lasso_bias_per_wsnow.append(np.mean(bias_lasso[wsnow_lasso_idx]))
    
    wsnow_nn_idx = np.where((wsnow_nn < (wsnow + 100)) & (wsnow_nn > wsnow))
    nn_bias_per_wsnow.append(np.mean(bias_nn[wsnow_nn_idx]))
    
lasso_bias_per_wsnow = np.asarray(lasso_bias_per_wsnow)
nn_bias_per_wsnow = np.asarray(nn_bias_per_wsnow)

# Bias per glacier summer snow
lasso_bias_per_ssnow, nn_bias_per_ssnow = [],[]
for ssnow in np.arange(-1500, 1500, 50):
#    import pdb; pdb.set_trace()
    ssnow_lasso_idx = np.where((ssnow_lasso < (ssnow + 50)) & (ssnow_lasso > ssnow))
    lasso_bias_per_ssnow.append(np.mean(bias_lasso[ssnow_lasso_idx]))
    
    ssnow_nn_idx = np.where((ssnow_nn < (ssnow + 50)) & (ssnow_nn > ssnow))
    nn_bias_per_ssnow.append(np.mean(bias_nn[ssnow_nn_idx]))
    
lasso_bias_per_ssnow = np.asarray(lasso_bias_per_ssnow)
nn_bias_per_ssnow = np.asarray(nn_bias_per_ssnow)

#
SMB_lasso_obs_idx = np.argsort(y)
SMB_lasso_obs = y[SMB_lasso_obs_idx]
bias_lasso = bias_lasso[SMB_lasso_obs_idx]
SMB_nn_obs_idx = np.argsort(y)
SMB_nn_obs = y[SMB_nn_obs_idx]
bias_nn = bias_nn[SMB_nn_obs_idx]


plasso = poly.Polynomial.fit(SMB_lasso_obs, bias_lasso, 6)
poly_lasso = np.asarray(plasso.linspace(n=SMB_lasso_obs.size))[1,:]
pnn = poly.Polynomial.fit(SMB_nn_obs, bias_nn, 6)
poly_nn = np.asarray(pnn.linspace(n=SMB_nn_obs.size))[1,:]

# KDE lasso
kde_x_lasso = np.linspace(lasso_prediction.min(), lasso_prediction.max(), 301)
kde_lasso = st.gaussian_kde(lasso_prediction)
kde_x_lasso_obs = np.linspace(SMB_lasso_obs.min(), SMB_lasso_obs.max(), 301)
kde_lasso_obs = st.gaussian_kde(SMB_lasso_obs)

# KDE DL
kde_x_nn = np.linspace(nn_prediction.min(), nn_prediction.max(), 301)
kde_nn = st.gaussian_kde(nn_prediction)
kde_x_nn_obs = np.linspace(SMB_nn_obs.min(), SMB_nn_obs.max(), 301)
kde_nn_obs = st.gaussian_kde(SMB_nn_obs)

# KDE Obs
kde_x_obs = np.linspace(y.min(), y.max(), 301)
kde_obs = st.gaussian_kde(nn_prediction)
kde_x_nn_obs = np.linspace(SMB_nn_obs.min(), SMB_nn_obs.max(), 301)
kde_nn_obs = st.gaussian_kde(SMB_nn_obs)

#
#print("\nRMSE Lasso: " + str(rmse_lasso))
#print("\nRMSE Deep learning: " + str(rmse_nn))
#
#import pdb; pdb.set_trace()
#
########   PLOTS  #########


fig2, ax2 = plot.subplots(ncols=1, nrows=2, axwidth=3, aspect=1.5, share=3)

ax2.format(
        abc=True, abcloc='ur', abcstyle='A',
        ygridminor=True,
        ytickloc='both', yticklabelloc='left',
        ylabel='Glacier-wide MB (m.w.e. a$^{-1}$)'
)

# Non-cumulative
ax2[0].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
#ax1[0].axvline(x=0, color='black', linewidth=0.7, linestyle='-')
ax2[1].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
#ax1[1].axvline(x=0, color='black', linewidth=0.7, linestyle='-')

ax2[0].plot(kde_x_lasso, kde_lasso(kde_x_lasso), c='tomato', linestyle='--', linewidth=3)
ax2[0].plot(kde_x_lasso_obs, kde_lasso_obs(kde_x_lasso_obs), c='darkred', linewidth=3)
ax2[0].set_ylim([0,1])

ax2[1].plot(kde_x_nn, kde_nn(kde_x_nn), c='denim', linestyle='--', linewidth=3, label='DL 100', legend='r')
ax2[1].plot(kde_x_nn_obs, kde_nn_obs(kde_x_nn_obs), c='midnightblue', linewidth=3, label='Obs', legend='r')
ax2[1].set_ylim([0,1])

#################################################################################

fig3, ax3 = plot.subplots([[1,1],[2,3],[4,5],[6,0],[7, 7]], ref=2, ncols=2, nrows=4, axwidth=3, aspect=2, sharex=0)

ax3.format(
        abc=True, abcloc='ul', abcstyle='A',
        ygridminor=True,
        ytickloc='both', yticklabelloc='left',
        ylabel='Bias (m.w.e. a$^{-1}$)'
)

# Non-cumulative
ax3[0].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
ax3[0].format(xlabel='Year')
ax3[0].bar(range(1959,2016), lasso_bias_per_year, alpha=0.5)
ax3[0].bar(range(1959,2016), nn_bias_per_year, alpha=0.5)

ax3[1].format(xlabel='Glacier area (km$^{2}$)')
ax3[1].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
ax3[1].plot(np.arange(0,33,0.25), lasso_bias_per_area, color='denim')
ax3[1].plot(np.arange(0,33,0.25), nn_bias_per_area, color='orange')
ax3[1].set_ylim([-2,2])
ax3[1].set_xlim([0,1])

ax3[2].format(xlabel='Glacier slope (°)')
ax3[2].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
ax3[2].plot(np.arange(0,50,2), lasso_bias_per_slope, color='denim')
ax3[2].plot(np.arange(0,50,2), nn_bias_per_slope, color='orange')
ax3[2].set_ylim([-2,2])
ax3[2].set_xlim([6,28])

ax3[3].format(xlabel='CPDD anomaly')
ax3[3].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
ax3[3].plot(np.arange(-1000,1000,100), lasso_bias_per_cpdd, color='denim')
ax3[3].plot(np.arange(-1000,1000,100), nn_bias_per_cpdd, color='orange')
ax3[3].set_ylim([-2,2])

ax3[4].format(xlabel='Winter snow anomaly (mm)')
ax3[4].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
ax3[4].plot(np.arange(-1500,1500,100), lasso_bias_per_wsnow, color='denim')
ax3[4].plot(np.arange(-1500,1500,100), nn_bias_per_wsnow, color='orange')
ax3[4].set_ylim([-2,2])

ax3[5].format(xlabel='Summer snow anomaly (mm)')
ax3[5].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
ax3[5].plot(np.arange(-1500,1500,50), lasso_bias_per_ssnow, color='denim')
ax3[5].plot(np.arange(-1500,1500,50), nn_bias_per_ssnow, color='orange')
ax3[5].set_ylim([-2,2])

ax3[6].format(xlabel='Glacier-wide MB (m.w.e. a$^{-1}$)')
ax3[6].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
ax3[6].plot(np.arange(-5,5,0.5), lasso_bias_per_MB, color='denim', label='Lasso', legend='ur')
ax3[6].plot(np.arange(-5,5,0.5), nn_bias_per_MB, color='orange', label='Deep learning', legend='ur')
ax3[6].set_ylim([-2,2])


##############   RECONSTRUCTION PLOTS   ##################

#import pdb; pdb.set_trace()

mask_lasso = np.isfinite(ds_smb_lasso_reconstructions.SMB.values.flatten())
finite_lasso = ds_smb_lasso_reconstructions.SMB.values.flatten()[mask_lasso]
mask_nn = np.isfinite(ds_smb_nn_reconstructions.SMB.values.flatten())
finite_nn = ds_smb_nn_reconstructions.SMB.values.flatten()

r_idx = np.argsort(finite_lasso)
lasso_ord_SMB = finite_lasso[r_idx]
DL_ord_SMB = finite_nn[r_idx]
p_r_lasso_DL = poly.Polynomial.fit(lasso_ord_SMB, DL_ord_SMB, 3)
poly_r_lasso_DL = np.asarray(p_r_lasso_DL.linspace(n=lasso_ord_SMB.size))

fig5, ax5 = plot.subplots(ncols=3, nrows=3, axwidth=2, aspect=1, share=0)

ax5.format(
        abc=True, abcloc='ul', abcstyle='A',
        ygridminor=True,
        ytickloc='both', yticklabelloc='left',
        xlabel='Lasso', ylabel='Deep learning'
)

# Deep learning vs obs
ax5[0].format(title='Deep learning vs Obs', xlabel='Obs')
ax5[0].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
ax5[0].axvline(x=0, color='black', linewidth=0.7, linestyle='-')
ax5[0].set_ylim([-4, 4])
ax5[0].scatter(y, nn_cv_prediction, c='forest green')
#ax5[0].plot(poly_r_lasso_DL, c='sienna')
ax5[0].plot([-4, 4], [-4, 4], c='k')

# Deep learning vs obs
ax5[1].format(title='Lasso vs Obs', xlabel='Obs', ylabel='Lasso')
ax5[1].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
ax5[1].axvline(x=0, color='black', linewidth=0.7, linestyle='-')
ax5[1].set_ylim([-4, 4])
ax5[1].scatter(y, lasso_prediction, c='sienna')
#ax5[0].plot(poly_r_lasso_DL, c='sienna')
ax5[1].plot([-4, 4], [-4, 4], c='k')

# 32 Glaciers with observations
ax5[2].format(title='Deep learning vs Lasso - 32 glaciers with Obs')
ax5[2].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
ax5[2].axvline(x=0, color='black', linewidth=0.7, linestyle='-')
ax5[2].set_ylim([-4, 4])
ax5[2].scatter(lasso_prediction, nn_cv_prediction, c='midnightblue')
#ax5[2].plot(poly_r_lasso_DL, c='sienna')
ax5[2].plot([-4, 4], [-4, 4], c='k')

# Deep learning vs obs 0.5 km2
ax5[3].format(title='Deep learning vs Obs < 0.5 km$^{2}$', xlabel='Obs')
ax5[3].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
ax5[3].axvline(x=0, color='black', linewidth=0.7, linestyle='-')
ax5[3].set_ylim([-4, 4])
ax5[3].scatter(y[rabatel_area_idx], nn_cv_prediction[rabatel_area_idx], c='forest green')
#ax5[0].plot(poly_r_lasso_DL, c='sienna')
ax5[3].plot([-4, 4], [-4, 4], c='k')

# Deep learning vs obs 0.5 km2
ax5[4].format(title='Lasso vs Obs < 0.5 km$^{2}$', xlabel='Obs', ylabel='Lasso')
ax5[4].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
ax5[4].axvline(x=0, color='black', linewidth=0.7, linestyle='-')
ax5[4].set_ylim([-4, 4])
ax5[4].scatter(y[rabatel_area_idx], lasso_prediction[rabatel_area_idx], c='sienna')
#ax5[0].plot(poly_r_lasso_DL, c='sienna')
ax5[4].plot([-4, 4], [-4, 4], c='k')

# 32 Glaciers with observations 0.5 km2
ax5[5].format(title='Deep learning vs Lasso - 32 glaciers < 0.5 km$^{2}$')
ax5[5].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
ax5[5].axvline(x=0, color='black', linewidth=0.7, linestyle='-')
ax5[5].set_ylim([-4, 4])
ax5[5].scatter(lasso_prediction[rabatel_area_idx], nn_cv_prediction[rabatel_area_idx], c='midnightblue')
#ax5[2].plot(poly_r_lasso_DL, c='sienna')
ax5[5].plot([-4, 4], [-4, 4], c='k')

# 1967-2015 reconstructions
ax5[6].format(title='Regional reconstructions')
ax5[6].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
ax5[6].axvline(x=0, color='black', linewidth=0.7, linestyle='-')
ax5[6].set_ylim([-4.5, 4])
ax5[6].scatter(ds_smb_lasso_reconstructions.SMB.values.flatten(), ds_smb_nn_reconstructions.SMB.values.flatten(), c='french blue')
#ax5[0].plot(poly_r_lasso_DL, c='sienna')
ax5[6].plot([-4.5, 4], [-4.5, 4], c='k')

#import pdb; pdb.set_trace()

# 1967-2015 Rabatel reconstructions
ax5[7].format(title='Regional reconstruction < 0.5 km$^{2}$')
ax5[7].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
ax5[7].axvline(x=0, color='black', linewidth=0.7, linestyle='-')
ax5[7].set_ylim([-4.5, 4])
ax5[7].scatter(ds_smb_lasso_reconstructions.SMB.values[small_area_idx].flatten(), ds_smb_nn_reconstructions.SMB.values[small_area_idx].flatten(), c='skyblue')
#ax5[1].plot(poly_r_lasso_DL, c='sienna')
ax5[7].plot([-4.5, 4], [-4.5, 4], c='k')

# 1967-2015 Rabatel reconstructions
ax5[8].format(title='Regional reconstruction - 32 glaciers with Obs')
ax5[8].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
ax5[8].axvline(x=0, color='black', linewidth=0.7, linestyle='-')
ax5[8].set_ylim([-4.5, 4])
ax5[8].scatter(ds_smb_lasso_reconstructions.SMB.values[rabatel_idxs].flatten(), ds_smb_nn_reconstructions.SMB.values[rabatel_idxs].flatten(), c='skyblue')
#ax5[1].plot(poly_r_lasso_DL, c='sienna')
ax5[8].plot([-4.5, 4], [-4.5, 4], c='k')

#####################################################

#import pdb; pdb.set_trace()

##### Deep learning bias per predictor  ##############

fig6, ax6 = plot.subplots(ncols=7, nrows=5, axwidth=1, aspect=1, sharex=0)

ax6.format(
        abc=True, abcloc='ul', abcstyle='A',
        ygridminor=True,
        ytickloc='both', yticklabelloc='left',
        ylabel='Bias (m.w.e. a$^{-1}$)'
)

idx = 0
for predictor_nn, predictor_lasso in zip(pred_nn['pred'], pred_lasso['pred']):
    
    if(idx==0):
        ax6[0].plot(np.arange(pred_lasso['pred'][0].min(), pred_lasso['pred'][0].max(), pred_lasso['steps'][0]), pred_lasso['bias'][0], label ='Lasso', legend='t')
        ax6[0].plot(np.arange(pred_nn['pred'][0].min(), pred_nn['pred'][0].max(), pred_nn['steps'][0]), pred_nn['bias'][0], label ='Deep learning', legend='t')
    else:
        ax6[idx].format(xlabel=pred_names[idx])
        ax6[idx].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
        ax6[idx].plot(np.arange(predictor_lasso.min(), predictor_lasso.max(), pred_lasso['steps'][idx]), pred_lasso['bias'][idx])
        ax6[idx].plot(np.arange(predictor_nn.min(), predictor_nn.max(), pred_nn['steps'][idx]), pred_nn['bias'][idx])
        ax6[idx].set_ylim([-2,2])
    
    idx = idx+1

################################

#####  Predictor distribution depending on glacier size  ######
    
fig7, ax7 = plot.subplots(ncols=7, nrows=5, axwidth=1, aspect=1, share=0)

ax7.format(
        abc=True, abcloc='ul', abcstyle='A',
        ygridminor=True,
        ytickloc='both', yticklabelloc='left',
        suptitle='Predictors depending on glacier area'
)

idx = 0
for s_pred, l_pred in zip(small_predictors[1:], large_predictors[1:]):
    
#    if(idx==0):
#        ax6[0].plot(np.arange(pred_lasso['pred'][0].min(), pred_lasso['pred'][0].max(), pred_lasso['steps'][0]), pred_lasso['bias'][0], label ='Lasso', legend='t')
#        ax6[0].plot(np.arange(pred_nn['pred'][0].min(), pred_nn['pred'][0].max(), pred_nn['steps'][0]), pred_nn['bias'][0], label ='Deep learning', legend='t')
#    else:
    
    data = [s_pred.astype(float).tolist(), l_pred.astype(float).tolist()]
    
    ax7[idx].format(title=pred_names_MB[idx])
#    ax7[idx].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
    bplot = ax7[idx].boxplot(data, labels=['Small', 'Large'], widths=0.75)
#    ax7[idx].set_ylim([-2,2])
    idx = idx+1
    
#    # fill with colors
#    colors = ['darkred', 'denim']
#    for patch, color in zip(bplot['boxes'], colors):
#        import pdb; pdb.set_trace()
#        patch.set(facecolor = color)


################################
    
#####  Predictor distribution depending on glacier altitude   ######
    
fig8, ax8 = plot.subplots(ncols=7, nrows=5, axwidth=1, aspect=1, share=0)

ax8.format(
        abc=True, abcloc='ul', abcstyle='A',
        ygridminor=True,
        ytickloc='both', yticklabelloc='left',
        suptitle='Predictors depending on glacier altitude'
#        ylabel='Bias (m.w.e. a$^{-1}$)'
)

idx = 0
for low_pred, high_pred in zip(high_zmean_predictors[1:], low_zmean_predictors[1:]):
    
#    if(idx==0):
#        ax6[0].plot(np.arange(pred_lasso['pred'][0].min(), pred_lasso['pred'][0].max(), pred_lasso['steps'][0]), pred_lasso['bias'][0], label ='Lasso', legend='t')
#        ax6[0].plot(np.arange(pred_nn['pred'][0].min(), pred_nn['pred'][0].max(), pred_nn['steps'][0]), pred_nn['bias'][0], label ='Deep learning', legend='t')
#    else:
    
    data = [low_pred.astype(float).tolist(), high_pred.astype(float).tolist()]
    
    ax8[idx].format(title=pred_names_MB[idx])
#    ax7[idx].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
    bplot = ax8[idx].boxplot(data, labels=['Low', 'High'], widths=0.75)
#    ax7[idx].set_ylim([-2,2])
    idx = idx+1
    
#    # fill with colors
#    colors = ['darkred', 'denim']
#    for patch, color in zip(bplot['boxes'], colors):
#        import pdb; pdb.set_trace()
#        patch.set(facecolor = color)
    
###############################################
    
#####  Predictor distribution depending on extreme positive MB values   ######
    
fig9, ax9 = plot.subplots(ncols=7, nrows=5, axwidth=1, aspect=1, share=0)

ax9.format(
        abc=True, abcloc='ul', abcstyle='A',
        ygridminor=True,
        ytickloc='both', yticklabelloc='left',
        suptitle='Predictors depending extreme positive MB values'
#        ylabel='Bias (m.w.e. a$^{-1}$)'
)

idx = 0
for pos_pred_nn, pos_pred_lasso in zip(ext_pos_MB_predictors[1:], ext_pos_MB_predictors_lasso[1:]):
    
#    if(idx==0):
#        ax6[0].plot(np.arange(pred_lasso['pred'][0].min(), pred_lasso['pred'][0].max(), pred_lasso['steps'][0]), pred_lasso['bias'][0], label ='Lasso', legend='t')
#        ax6[0].plot(np.arange(pred_nn['pred'][0].min(), pred_nn['pred'][0].max(), pred_nn['steps'][0]), pred_nn['bias'][0], label ='Deep learning', legend='t')
#    else:
    
    data = [pos_pred_nn.astype(float).tolist(), pos_pred_lasso.astype(float).tolist()]
    
    ax9[idx].format(title=pred_names_MB[idx])
#    ax7[idx].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
    bplot = ax9[idx].boxplot(data, labels=['DL', 'Lasso'], widths=0.75)
#    ax7[idx].set_ylim([-2,2])
    idx = idx+1
    
#    # fill with colors
#    colors = ['darkred', 'denim']
#    for patch, color in zip(bplot['boxes'], colors):
#        import pdb; pdb.set_trace()
#        patch.set(facecolor = color)


###################################################
    
  #####  Predictor distribution depending on extreme positive MB values   ######
    
fig10, ax10 = plot.subplots(ncols=7, nrows=5, axwidth=1, aspect=1, share=0)

ax10.format(
        abc=True, abcloc='ul', abcstyle='A',
        ygridminor=True,
        ytickloc='both', yticklabelloc='left',
        suptitle='Predictors depending extreme negative MB values'
#        ylabel='Bias (m.w.e. a$^{-1}$)'
)

idx = 0
for neg_pred_nn, neg_pred_lasso in zip(ext_neg_MB_predictors[1:], ext_neg_MB_predictors_lasso[1:]):
    
#    if(idx==0):
#        ax6[0].plot(np.arange(pred_lasso['pred'][0].min(), pred_lasso['pred'][0].max(), pred_lasso['steps'][0]), pred_lasso['bias'][0], label ='Lasso', legend='t')
#        ax6[0].plot(np.arange(pred_nn['pred'][0].min(), pred_nn['pred'][0].max(), pred_nn['steps'][0]), pred_nn['bias'][0], label ='Deep learning', legend='t')
#    else:
    
    data = [neg_pred_nn.astype(float).tolist(), neg_pred_lasso.astype(float).tolist()]
    
    ax10[idx].format(title=pred_names_MB[idx])
#    ax7[idx].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
    bplot = ax10[idx].boxplot(data, labels=['DL', 'Lasso'], widths=0.75)
#    ax7[idx].set_ylim([-2,2])
    idx = idx+1
    
#    # fill with colors
#    colors = ['darkred', 'denim']
#    for patch, color in zip(bplot['boxes'], colors):
#        import pdb; pdb.set_trace()
#        patch.set(facecolor = color)
  

####################################################
    
    
    
fig11, ax11 = plot.subplots(ncols=2, nrows=2, axwidth=2, aspect=1)

ax11.format(
        abc=True, abcloc='ul', abcstyle='A',
        ygridminor=True,
        ytickloc='both', yticklabelloc='left',
        xlabel='Lasso', ylabel='Deep learning'
)

# Small glaciers
ax11[0].format(title='Regional reconstruction < 0.5 km$^{2}$')
ax11[0].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
ax11[0].axvline(x=0, color='black', linewidth=0.7, linestyle='-')
ax11[0].set_ylim([-4.5, 4])
ax11[0].scatter(ds_smb_lasso_reconstructions.SMB.values[small_area_idx].flatten(), ds_smb_nn_reconstructions.SMB.values[small_area_idx].flatten(), c='skyblue')
#ax11[1].plot(poly_r_lasso_DL, c='sienna')
ax11[0].plot([-4.5, 4], [-4.5, 4], c='k')

# Large glaciers
ax11[1].format(title='Regional reconstruction > 0.5 km$^{2}$')
ax11[1].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
ax11[1].axvline(x=0, color='black', linewidth=0.7, linestyle='-')
ax11[1].set_ylim([-4.5, 4])
ax11[1].scatter(ds_smb_lasso_reconstructions.SMB.values[large_area_idx].flatten(), ds_smb_nn_reconstructions.SMB.values[large_area_idx].flatten(), c='skyblue')
#ax11[1].plot(poly_r_lasso_DL, c='sienna')
ax11[1].plot([-4.5, 4], [-4.5, 4], c='k')

# 1967-2015 Rabatel reconstructions
ax11[2].format(title='Regional reconstruction > 3000 m')
ax11[2].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
ax11[2].axvline(x=0, color='black', linewidth=0.7, linestyle='-')
ax11[2].set_ylim([-4.5, 4])
ax11[2].scatter(ds_smb_lasso_reconstructions.SMB.values[high_zmean_idx].flatten(), ds_smb_nn_reconstructions.SMB.values[high_zmean_idx].flatten(), c='skyblue')
#ax11[1].plot(poly_r_lasso_DL, c='sienna')
ax11[2].plot([-4.5, 4], [-4.5, 4], c='k')

# Low glaciers
ax11[3].format(title='Regional reconstruction < 3000 m')
ax11[3].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
ax11[3].axvline(x=0, color='black', linewidth=0.7, linestyle='-')
ax11[3].set_ylim([-4.5, 4])
ax11[3].scatter(ds_smb_lasso_reconstructions.SMB.values[low_zmean_idx].flatten(), ds_smb_nn_reconstructions.SMB.values[low_zmean_idx].flatten(), c='skyblue')
#ax11[1].plot(poly_r_lasso_DL, c='sienna')
ax11[3].plot([-4.5, 4], [-4.5, 4], c='k')

#################################################

#fig6, ax6 = plot.subplots(ncols=1, nrows=2, axwidth=3, aspect=0.8, share=0)
#
#ax6.format(
#        abc=True, abcloc='ul', abcstyle='A',
#        ygridminor=True,
#        ytickloc='both', yticklabelloc='left',
#)
#
## Deep learning vs obs
#ax6[0].format(title='Deep learning vs Obs during CV training', xlabel='Obs')
#ax6[0].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
#ax6[0].axvline(x=0, color='black', linewidth=0.7, linestyle='-')
#ax6[0].set_ylim([-4, 4])
#ax6[0].scatter(SMB_nn_obs_CV, SMB_nn_all_CV, c='forest green')
##ax6[0].plot(poly_r_lasso_DL, c='sienna')
#ax6[0].plot([-4, 4], [-4, 4], c='k')
#
## Deep learning vs obs
#ax6[1].format(title='Lasso vs Obs', xlabel='Obs', ylabel='Lasso')
#ax6[1].axhline(y=0, color='black', linewidth=0.7, linestyle='-')
#ax6[1].axvline(x=0, color='black', linewidth=0.7, linestyle='-')
#ax6[1].set_ylim([-4, 4])
#ax6[1].scatter(SMB_lasso_obs_CV, SMB_lasso_all_CV, c='sienna')
##ax6[0].plot(poly_r_lasso_DL, c='sienna')
#ax6[1].plot([-4, 4], [-4, 4], c='k')


plt.show()