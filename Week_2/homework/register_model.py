import os
import pickle
import click
import mlflow

from mlflow.entities import ViewType
from mlflow.tracking import MlflowClient
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from mlflow.models.signature import infer_signature

HPO_EXPERIMENT_NAME = "random-forest-hyperopt"
EXPERIMENT_NAME = "random-forest-best-models"
RF_PARAMS = ['max_depth', 'n_estimators', 'min_samples_split', 'min_samples_leaf', 'random_state', 'n_jobs']

mlflow.set_tracking_uri("http://127.0.0.1:5000")
mlflow.set_experiment(EXPERIMENT_NAME)
mlflow.sklearn.autolog()


def load_pickle(filename):
    with open(filename, "rb") as f_in:
        return pickle.load(f_in)


def train_and_log_model(data_path, params):
    X_train, y_train = load_pickle(os.path.join(data_path, "train.pkl"))
    X_val, y_val = load_pickle(os.path.join(data_path, "val.pkl"))
    X_test, y_test = load_pickle(os.path.join(data_path, "test.pkl"))

    with mlflow.start_run():
        for param in RF_PARAMS:
            params[param] = int(params[param])

        rf = RandomForestRegressor(**params)
        rf.fit(X_train, y_train)

        # Evaluate model on the validation and test sets
        val_rmse = mean_squared_error(y_val, rf.predict(X_val), squared=False)
        mlflow.log_metric("val_rmse", val_rmse)
        test_rmse = mean_squared_error(y_test, rf.predict(X_test), squared=False)
        mlflow.log_metric("test_rmse", test_rmse)
        
        y_pred = rf.predict(X_val)
        signature = infer_signature(X_test, y_pred)

        
        with open("models/rand_forest.bin", "wb") as f_out:
                pickle.dump(X_train, f_out)
        mlflow.log_artifact("models/rand_forest.bin", artifact_path="model_pickle")
        mlflow.sklearn.log_model(
            sk_model=rf,
            artifact_path="sklearn-model",
            signature=signature,
            registered_model_name="sk-learn-random-forest-reg-model",
        )


@click.command()
@click.option(
    "--data_path",
    default="./output",
    help="Location where the processed NYC taxi trip data was saved"
)
@click.option(
    "--top_n",
    default=5,
    type=int,
    help="Number of top models that need to be evaluated to decide which one to promote"
)
def run_register_model(data_path: str, top_n: int):

    client = MlflowClient()

    # # Retrieve the top_n model runs and log the models
    # experiment = client.get_experiment_by_name(HPO_EXPERIMENT_NAME)
    # runs = client.search_runs(
    #     experiment_ids=experiment.experiment_id,
    #     run_view_type=ViewType.ACTIVE_ONLY,
    #     max_results=top_n,
    #     order_by=["metrics.rmse DESC"]
    # )
    # for run in runs:
    #     train_and_log_model(data_path=data_path, params=run.data.params)

    # Select the model with the lowest test RMSE
    experiment = client.get_experiment_by_name(HPO_EXPERIMENT_NAME)
    best_run = client.search_runs(
        experiment_ids=experiment.experiment_id,
        filter_string="",
        run_view_type=ViewType.ACTIVE_ONLY,
        max_results=1,
        order_by=["metrics.test_rmse DESC"],
    )[0]


    print("!!!!!!!!!!!!!!!!!")
    print(best_run._info.run_id)
    print("!!!!!!!!!!!!!!!!!")
    
    # Register the best model
    mlflow.register_model(
    f'runs:/{best_run._info.run_id}/{RandomForestRegressor}', "HPO_EXPERIMENT_NAME"
)


if __name__ == '__main__':
    test = run_register_model()
