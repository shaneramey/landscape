import os
import yaml

class LandscaperDirCollection(object):
    """ Loads up a directory of chart yaml for use by Landscaper"""
    def __init__(self, chart_set_containing_namespaces):
        self.chartset_root_dir = chart_set_containing_namespaces
        print("A chart_set_containing_namespaces={0}".format(chart_set_containing_namespaces))
        self.chart_sets = self.__load_chart_sets()


    def __str__(self):
        return self.chartset_root_dir

    def __load_chart_sets(self):
        path_to_chartset_root_dir = self.chartset_root_dir
        chart_sets = {}
        print("path_to_chartset_root_dir={0}".format(path_to_chartset_root_dir))
        for chart_set in os.listdir(path_to_chartset_root_dir):
            print("chart_set={0}".format(chart_set))
            path_to_namespace_dir = path_to_chartset_root_dir + '/' + chart_set
            for namespace in os.listdir(path_to_namespace_dir):
                namespace_dir = path_to_namespace_dir + '/' + namespace 
                for chart_definition in os.listdir(namespace_dir):
                    path_to_chart_def = namespace_dir + '/' + chart_definition
                    with open(path_to_chart_def) as f:
                        chart_info = yaml.load(f)
                        chart_sets[chart_definition] = chart_info
        return chart_info

                    # print("chart_definition={0}".format(chart_definition))
                # landscaper_chart_def = chart_set_containing_namespaces + '/' + chart_set_dir + '/' + namespace_dir + '/' + landscaper_yaml
                # print("chart_definition={0}".format(landscaper_chart_def))
