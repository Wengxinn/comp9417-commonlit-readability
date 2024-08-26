# -*- coding: utf-8 -*-
"""
Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1LmrUI_mwMiQgMj0ACxyOBUSVQc_zXqyZ

COMP9417 Group Project (Topic 2)
Task: CommonLit Readability Prize
COMP9417_LR_SVR: Fit the model with Linear Regression and Support Vector Regression

Written by WENG XINN CHOW (z5346077)
"""

from google.colab import files

# Upload the dataset train.csv
files.upload()

# Commented out IPython magic to ensure Python compatibility.
# Import all required libraries
# %matplotlib inline
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.api as sm
from sklearn.linear_model import Ridge
from sklearn.svm import SVR
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error as mse

# Read train.csv file and display the first 5 rows
df = pd.read_csv("train_features.csv")
df.head()

# Plot a distribution of target scores and formate the plot (Set histogram and gaussian kernel estimates to True)
fig, ax = plt.subplots(figsize=(12, 6))
target_dist = sns.distplot(df['target'], hist = True, kde = True, hist_kws={'edgecolor':'black'},
             kde_kws={'linewidth': 5}, ax = ax)
target_dist.set_title('Distribution of Target Scores', fontsize = 15)
target_dist.set_xlabel('Target', fontsize = 12)
target_dist.set_ylabel('Density', fontsize = 12)

# Plot a distribution of standard error and formate the plot (Set histogram and gaussian kernel estimates to True)
fig, ax = plt.subplots(figsize=(12, 6))
std_error_dist = sns.distplot(df['standard_error'], hist = True, kde = True, hist_kws={'edgecolor':'black'},
             kde_kws={'linewidth': 5}, ax = ax)
std_error_dist.set_title('Distribution of Standard Errors', fontsize = 15)
std_error_dist.set_xlabel('Standard Error', fontsize = 12)
std_error_dist.set_ylabel('Density', fontsize = 12)

# Plot a scatter plot showing the relationship between target and standard errors and format the plot
plt.figure(figsize = (12, 6))
plt.scatter(df['target'], df['standard_error'])
plt.title('Standard Errors against Target Scores', fontsize = 15)
plt.xlabel('Target', fontsize = 12)
plt.ylabel('Standard Error', fontsize = 12)

def splitting_data(df):
    """
    Split the dataset into training and test sets
    """

    # Retrieve the values of X(features) and y(target) and split them into training and test sets
    features = df.drop(columns = ['excerpt', 'target', 'standard_error'])
    X = features.iloc[:].values
    y = df['target'].values
    X_train, X_true_test, y_train, y_true_test = train_test_split(X, y, test_size = 0.3, random_state = 42)
    
    return X_train, X_true_test, y_train, y_true_test

# Split the data and print the shape
X_train, X_true_test, y_train, y_true_test = splitting_data(df)
print(X_train.shape, X_true_test.shape)
print(y_train.shape, y_true_test.shape)

def ridge_grid(parameters):
    """
    Run grid search of ridge regression for given parameters
    """

    r_model = Ridge()
    ridge = GridSearchCV(estimator = r_model, param_grid = parameters, cv = 5, scoring = 'neg_root_mean_squared_error')
    ridge.fit(X_train, y_train)

    best_parameter = ridge.best_params_
    best_score = ridge.best_score_

    # Convert the cv results into a dataframe and sort the data by rank test scors
    ridge_df = pd.DataFrame(ridge.cv_results_)
    ridge_df = ridge_df.drop(columns = ['mean_fit_time', 'std_fit_time', 'mean_score_time', 'std_score_time', 'std_test_score'])
    ridge_df = ridge_df.sort_values(by = ['rank_test_score'])
    ridge_df = ridge_df.rename(columns = {'param_alpha': 'alpha', 'params': 'parameters', 'split0_test_score': 'cv_score_1', 
                                        'split1_test_score': 'cv_score_2', 'split2_test_score': 'cv_score_3', 'split3_test_score': 'cv_score_4', 
                                        'split4_test_score': 'cv_score_5', 'mean_test_score': 'RMSE', 'rank_test_score': 'rank'})
    ridge_df.set_index('rank', inplace = True)

    return ridge_df, best_parameter

# Initialize the regression parameters for grid search
params = {'alpha': [0.0001, 0.001, 0.01, 0.1, 1, 10, 100]}

ridge_df, parameters = ridge_grid(params)
ridge_model = Ridge(alpha = parameters.get('alpha'))
ridge_model.fit(X_train, y_train)

# Fit the model with the best hyperparameters and get the train and test rmse
y_train_pred = ridge_model.predict(X_train)
ridge_train_rmse = mse(y_train, y_train_pred, squared = False)
ridge_y_true_test_pred = ridge_model.predict(X_true_test)
ridge_true_test_rmse = mse(y_true_test, ridge_y_true_test_pred, squared = False)
print('Train and true test RMSE for ridge regresison: ', ridge_train_rmse, ',', ridge_true_test_rmse)

# Display results of cv in a table
# Absolute values for cv scores and mse (dictionary has no absolute function)
ridge_df_abs = ridge_df.drop(columns = ['parameters']).abs()
ridge_df = pd.concat([ridge_df.drop(columns = ['cv_score_1', 'cv_score_2', 'cv_score_3', 'cv_score_4', 'cv_score_5', 'RMSE']), 
                       ridge_df_abs], join = 'outer', axis = 1)
ridge_df

# Find the cofficient for each feature and return the statsmodel summary 
# To print the summary, we need to fit OLS model (it only has OLS model as parameters)
model = sm.OLS(y_train, X_train)
stats_OLS = model.fit()

# Fit regularized OLS model (ridge-> L1_wt = 0), use the optimal alpha-> 1 
# start_params is the starting values for parameter (penalty)
stats_ridge = model.fit_regularized(L1_wt = 0, alpha = 1, start_params = stats_OLS.params)

# Result class for OLS model (model can only be OLS model, but the estimated parameters is from ridge regression) 
result = sm.regression.linear_model.OLSResults(model = model, params = stats_ridge.params, normalized_cov_params = model.normalized_cov_params)
result_summary = result.summary()

# Convert the summary into a dataframe
result_html = result_summary.tables[1].as_html()
result_df = pd.read_html(result_html, header = 0, index_col = 0)[0]
result_df.columns = ['Coefficients', 'Standard Error', 't-value', 'p-value', 'Lower CI (2.5%)', 'Higher CI (97.5%)']
result_df.index = list(features.columns)

# Drop the row that has p-value >= 0.05
result_df = result_df[result_df['p-value'] < 0.05]
result_df

# Plot a horizontal bar chart of features' coefficients
plt.figure(figsize = (10, 8))
plt.barh(result_df.index, result_df['Coefficients'])
plt.title('Coefficients', fontsize = 15)
plt.xlabel('Coefficients', fontsize = 12)
plt.ylabel('Features', fontsize = 12)

def svr_grid(parameters):
    """
    Run grid search of svm for given parameters
    """

    # Hyperparameter tuning for svm
    svr_model = SVR()
    svr = GridSearchCV(estimator = svr_model, param_grid = parameters, cv = 5, scoring = 'neg_root_mean_squared_error')
    svr.fit(X_train, y_train)

    best_parameter = svr.best_params_
    best_score = svr.best_score_

     # Convert the cv results into a dataframe and sort the data by rank test scors
    svr_df = pd.DataFrame(svr.cv_results_)
    svr_df = svr_df.drop(columns = ['mean_fit_time', 'std_fit_time', 'mean_score_time', 'std_score_time', 'std_test_score'])
    svr_df = svr_df.sort_values(by = ['rank_test_score'])
    svr_df = svr_df.rename(columns = {'param_C': 'C', 'param_kernel': 'kernel', 'params': 'parameters', 'split0_test_score': 'cv_score_1', 
                                        'split1_test_score': 'cv_score_2', 'split2_test_score': 'cv_score_3', 'split3_test_score': 'cv_score_4', 
                                        'split4_test_score': 'cv_score_5', 'mean_test_score': 'RMSE', 'rank_test_score': 'rank'})
    svr_df.set_index('rank', inplace = True)

    return svr_df, best_parameter

# Initialize svr parameters for grid search
svr_params = {'C': [0.001, 0.01, 0.1, 1, 10], 'kernel': ('linear', 'rbf')}
svr_df, parameters = svr_grid(svr_params)
svr_model = SVR(C = parameters.get('C'), kernel = parameters.get('kernel'))
svr_model.fit(X_train, y_train)

y_train_pred = svr_model.predict(X_train)
svr_train_rmse = mse(y_train, y_train_pred, squared = False)
svr_y_true_test_pred = svr_model.predict(X_true_test)
svr_true_test_rmse = mse(y_true_test, svr_y_true_test_pred, squared = False)
print('Train and true test RMSE for SVR: ', svr_train_rmse, ',', svr_true_test_rmse)

# Display results of cv in a table
# Absolute values for cv scores and mse (dictionary has no absolute function)
svr_df_abs = svr_df.drop(columns = ['parameters', 'kernel', 'C']).abs()
svr_df = pd.concat([svr_df.drop(columns = ['cv_score_1', 'cv_score_2', 'cv_score_3', 'cv_score_4', 'cv_score_5', 'RMSE']), 
                       svr_df_abs], join = 'outer', axis = 1)
svr_df

# Create result files 
# Need to combine the original train file because features file don't show some of the information 
original_df = pd.read_csv('train.csv')
original_df.head()

original_train = original_df.loc[1983:]
original_train = original_train.reset_index(drop = True)
original_train.head()

# Result file for ridge regression prediction
ridge_result = pd.DataFrame(ridge_y_true_test_pred, columns = ['predict'])
result_ridge = pd.concat([original_train, ridge_result], axis = 1, join = 'outer')
result_ridge.head()

# Result file for svr prediction
svr_result = pd.DataFrame(svr_y_true_test_pred, columns = ['predict'])
result_svr = pd.concat([original_train, svr_result], axis = 1, join = 'outer')
result_svr.head()

# Save and downloads csv file
result_ridge.to_csv('test_prediction_ridge.csv')
result_svr.to_csv('test_prediction_svr.csv')

files.download('test_prediction_ridge.csv')
files.download('test_prediction_svr.csv')
