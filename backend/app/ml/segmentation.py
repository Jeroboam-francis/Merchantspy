import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def segment_merchants(merchant_metrics: list[dict]) -> list[dict]:
    if len(merchant_metrics) < 2:
        raise ValueError("At least two merchants are required for portfolio segmentation")
    features = np.asarray([
        [np.log1p(max(0.0, float(row["revenue"]))),
         np.log1p(max(0.0, float(row["transactions"]))),
         np.log1p(max(0.0, float(row["subscribers"]))),
         max(-100.0, min(100.0, float(row["growth_rate"])))]
        for row in merchant_metrics
    ])
    scaled = StandardScaler().fit_transform(features)
    cluster_count = min(4, len(merchant_metrics))
    model = KMeans(n_clusters=cluster_count, random_state=17, n_init=10)
    cluster_ids = model.fit_predict(scaled)
    order = sorted(range(cluster_count), key=lambda cluster: float(np.mean(model.cluster_centers_[cluster])))
    names = {
        2: ("developing", "leading"),
        3: ("developing", "emerging", "leading"),
        4: ("developing", "emerging", "established", "leading"),
    }[cluster_count]
    labels = {cluster: names[index] for index, cluster in enumerate(order)}
    return [
        {"merchant_id": row["id"], "segment": labels[int(cluster_ids[index])],
         "cluster": int(cluster_ids[index]), "grade": row["grade"], "score": row["score"]}
        for index, row in enumerate(merchant_metrics)
    ]
