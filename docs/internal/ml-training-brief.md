We need to move Sentinel Anti-Cheat into the ML training phase.

Your task is to design and implement a full ML training pipeline for the anomaly detection layer used in the evidence report system.

Goals
Build a reproducible training workflow that produces the following artifacts:

backend/models/xgboost/v1.0/xgboost_model.json
backend/models/isolation_forest/v1.0/isolation_forest.pkl

The training pipeline should include:

1. Dataset ingestion

* Accept PGN datasets or extracted move feature datasets.
* If no real dataset is available, tell me so i can add dataset so the pipeline can run end-to-end. check C:\Users\Accountant\Desktop\Abdul\SentinelAntiCheat\backend\data IF THE GAMES EXIST ELSE TELL ME SO I CAN ADD THEM OR IF U CAN U CAN GET THEM ONLINE 

2. Feature construction
   Use features derived from the Sentinel analysis pipeline such as:

* engine_match_percentage
* maia_agreement_percentage
* centipawn_loss
* move_complexity
* move_number
* blunder_rate
* tactical_accuracy
* position_difficulty

3. Model training
   Train two models:

* XGBoost classifier
* Isolation Forest anomaly detector

4. Model persistence
   Save trained models to:
   backend/models/xgboost/v1.0/xgboost_model.json
   backend/models/isolation_forest/v1.0/isolation_forest.pkl

Use:

* XGBoost save_model()
* joblib.dump() for IsolationForest.

5. Evaluation
   Print evaluation metrics such as:

* anomaly score distribution
* classification accuracy (if labels exist)
* feature importance

6. System integration check
   After training, automatically verify that Sentinel loads the models successfully by calling /v1/system-status.

7. Manual input checkpoints
   If any of the following decisions are required, stop and request my input:

* dataset selection or PGN source
* feature list approval
* model hyperparameters
* training size limits
* model versioning

8. Training command
   Create a script:
   backend/scripts/train_models.py

This script should run with:

python backend/scripts/train_models.py

and produce the required model artifacts.

Goal
Once completed, Sentinel should report:

ml_models_loaded: true
analysis_pipeline_operational: trueImportant design constraint for Sentinel Anti-Cheat:

The ML models must not be trained to classify games or players as "cheating" or "not cheating".

Instead, the ML models should model statistical deviations from expected human play.

Training objectives:

1. Isolation Forest
   Use it as an unsupervised anomaly detector trained on normal human game features. The model should learn the distribution of typical human play patterns.

2. XGBoost
   If labels are used, they should represent statistical categories such as:

* typical human play
* unusual statistical deviation

Do not create labels such as "cheater" or "fair player".

3. Engine signals
   Engine agreement metrics should be treated as just one feature among many and must not dominate the model.

4. Human-style modeling
   Maia agreement scores should be a key feature representing expected human decision patterns.

5. Output
   The ML layer should output:

* anomaly score
* deviation indicators
* feature contribution signals

These outputs will feed the Arbiter Evidence Report and must not produce accusations or cheating classifications.

The final system output should remain neutral and informational for arbiter interpretation.
THIS IS A HYBRID MODEL  