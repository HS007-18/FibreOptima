import yaml
import os

class DataLeakageError(Exception):
    """Raised when a subsystem tries to access a dataset it is not allowed to."""
    pass

class DatasetProvenanceRegistry:
    def __init__(self, manifest_path: str = "data/manifest.yaml"):
        # Resolve path relative to the root project directory (assuming src is in root)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if not os.path.isabs(manifest_path):
            manifest_path = os.path.join(project_root, manifest_path)
            
        with open(manifest_path, 'r') as f:
            self.manifest = yaml.safe_load(f)
            
        if "datasets" not in self.manifest:
            raise ValueError("Manifest must contain a 'datasets' root key.")

    def get_dataset_path(self, dataset_name: str, consumer_context: str) -> str:
        """
        Returns the path to the dataset if the consumer is allowed to access it.
        Raises DataLeakageError if the consumer is forbidden or not explicitly allowed.
        """
        datasets = self.manifest["datasets"]
        if dataset_name not in datasets:
            raise KeyError(f"Dataset '{dataset_name}' not found in manifest.")
            
        dataset = datasets[dataset_name]
        
        forbidden = dataset.get("forbidden", [])
        if consumer_context in forbidden:
            raise DataLeakageError(f"CRITICAL: Consumer '{consumer_context}' is strictly forbidden from accessing '{dataset_name}'.")
            
        allowed = dataset.get("allowed", [])
        if consumer_context not in allowed:
            raise DataLeakageError(f"SECURITY: Consumer '{consumer_context}' is not explicitly allowed to access '{dataset_name}'.")
            
        path = dataset["path"]
        
        # Make the path absolute relative to project root so it loads robustly from anywhere
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if not os.path.isabs(path):
            path = os.path.join(project_root, path)
            
        return path

# Singleton for easy access
registry = DatasetProvenanceRegistry()
