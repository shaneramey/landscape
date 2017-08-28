import os
import glob
import yaml

class LandscaperChartsCollection(object):
    """ Loads up a directory of chart yaml for use by Landscaper
    vault write /secret/landscape/clouds/staging-165617 provisioner=terraform
    vault write /secret/landscape/clouds/minikube provisioner=minikube
    """
    def __init__(self, landscaper_chart_root):
        self.chartset_root_dir = landscaper_chart_root
        print("A chart_set_containing_namespaces={0}".format(chart_set_containing_namespaces))
        self.chart_collections = ['__all_clusters__'] + ['minikube']
        self.chart_sets = self.__load_chart_sets()

    def __str__(self):
        return self.chartset_root_dir

    def __load_chart_sets(self):
        path_to_chartset_root_dir = self.chartset_root_dir
        chart_sets = {}
        print("path_to_chartset_root_dir={0}".format(path_to_chartset_root_dir))
        for chart_set in os.listdir(path_to_chartset_root_dir):
            if chart_set in self.chart_collections:
                print("chart_set={0}".format(chart_set))
                chart_sets[chart_set] = {}
                chart_set_charts = [file for file in glob.glob(path_to_chartset_root_dir + '/' + chart_set + '/**/*.yaml', recursive=True)]
                print("chart_set_charts={0}".format(chart_set_charts))
                for landscaper_yaml in chart_set_charts:
                    with open(landscaper_yaml) as f:
                        chart_info = yaml.load(f)
                        chart_name = chart_info['name']
                        chart_namespace = chart_info['namespace']
                        chart_info['landscaper_yaml_path'] = landscaper_yaml
                        if not chart_namespace in chart_sets[chart_set]:
                            chart_sets[chart_set][chart_namespace] = {}
                        chart_sets[chart_set][chart_namespace][chart_name] = chart_info
        return chart_sets