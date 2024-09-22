# How to Setup the Config File

This document highlights the most important fields in the configuration file. 

Those with 🔴 are important config options that should be checked before running any optimization job. 

## 1. cuGraph_to_pos_df
This section contains configurations for transforming the graph file into a position dataframe using cuGraph's forceatlas2 layout algorithm.

> 🔴Note: Refer to `Sample Graph Generation Tutorial.md` for more details on the graph inputting format for the GraphOptima framework.

- **🔴GRAPHML_FILE**: The GraphML file path. Note: Test GraphML files were generated using [graph-tool](https://graph-tool.skewed.de/).
- **🔴CSV_FILE**: The destination CSV file path. The CSV is in the edgelist format.
- **CSV_COLUMNS**: Column names to be used in the CSV file.
- **CSV_SOURCE** and **CSV_DESTINATION**: Source and destination node column names, respectively.
- **CSV_DTYPES**: Data types for the CSV columns.
- **SEPARATOR**: Character used for field separation in the CSV file.
- **CUDF_EDGELIST_SLICE**: Slice of the edgelist to be converted into a dataframe.
- **DEBUG**: Enable or disable debug mode (true/false).

## 2. external_api
Settings related to the External API.

- **INSTRUCTION_PATH**: Directory where to save API's instructions.
- **MAIL**: Contains email notification settings.
  - **FROM** and **TO**: Sender and receiver's email addresses.
  - **SMTP_SERVER** and **SMTP_PORT**: SMTP server details.
  - **KEY_PATH**: The path to your `key` file. See `Setting up email notification.md` for more details.
  - **KEY**: Email encryption key details.
- **SLURM**: Settings for Slurm jobs.
  - **🔴NUM_LAYOUT_GENERATOR**, **NUM_LAYOUT_EVALUATOR**, **NUM_OPTIMIZER**, **NUM_EXTERNAL_API**: Number of each job called.
  - **UPDATE_INTERVAL**: Time (in seconds) between Slurm updates.
- **EVENT_LOG_DISPLAY_LINES**: Number of log lines to display.

## 3. optimization_database
Settings for the optimization database.

- **DATABASE_PATH**: Path to the database file.
- **MAX_ERROR_PERCENTAGE**: Maximum allowed percentage of errors.
- **COSINE_SIMILARITY_THRESHOLD**: Threshold for cosine similarity.

## 4. optimizer
Settings for the optimizer.

- **🔴SINGLE_OBJECTIVE_OPTIMIZATION**: Enable/disable single-objective optimization.
- **MAX_ALLOWABLE_ERROR_RETRY**: Maximum number of retries in case of an error.
- **DATABASE_WRITE_FREQUENCY**: Frequency for writing to the database.
- **METADATA**: Settings for the optimization.
- **🔴OPTIMIZATION_BUDGET**: Budget for optimization. Refer to the [scipy.differential_evolution](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html) documentation for more details.
- **SUBSTITUTION_BY_FINDING_SIMILAR_TESTED_PARAM**: Enable/disable substitution by finding similar tested parameters.
- **SUBSTITUTION_BY_FINDING_EXACT_TESTED_ITERATION_NUM**: Enable/disable substitution by finding exact tested iteration numbers.
- **BREAKPOINT_SKIP**: What to do when resuming from a breakpoint: Skip all the tested weighting schemes or rerun all the tested weighting schemes (true/false).
- **REWARD**: The reward function.
- **BOUNDS**: Boundaries for the optimization parameters.
- **INITIAL_GUESS**: Initial guess for the optimization parameters.
- **NUM_OF_DESIGN_PARAMS** and **NUM_OF_OBJECTIVE_PARAMS**: Number of design and objective parameters, respectively.
- **differential_evolution_optimization_params**: Settings for differential evolution optimization.
- **🔴email_notification**: Settings for email notifications related to the optimization process (true/false).
- **🔴scalarization_granularity**: Sets the granularity for scalarization in the multivariable optimization process.

## 5. verify_optimized_params
Settings for the verification of optimized parameters.

- **REPEAT_EVAL_TIMES**: Number of times to repeat the evaluation process for verification.
- **🔴PLOT_RESOLUTION**: Resolution for the output plot.

## 6. reward
Settings for the reward calculation.

- **🔴CROSSLESSNESS_WEIGHT**, **NUM_EDGE_CROSSINGS_WEIGHT**, **EDGE_LENGTH_CV_WEIGHT**, **NORMALIZED_CV_WEIGHT**, **MIN_ANGLE_WEIGHT**, **SHAPE_DELAUNAY_WEIGHT**, **SHAPE_GABRIEL_WEIGHT**: Weights given to each component in the reward calculation. The weights (such as crosslessness, edge crossing, and edge length CV) are set as default. To exclude a weight from optimization, set it to zero.
- **FORMULA**: Formula for reward calculation.

## 7. dot_to_readability_score
Settings for converting DOT language graphs to readability scores.

- **DEBUG**: Enable or disable debug mode (true/false).
- **GLAM_PATH**: Path to the GLAM (Graph Layout Aesthetics Metrics) tool. See `Setting up GLAM layout evaluator.md` for more details.
