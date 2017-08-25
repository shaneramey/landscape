class ChartSetCollection(object):

    def __init__(self):
        self.__chart_sets = self.chart_sets()


    def chart_sets(self):
        for chart_set in os.listdir:
            for namespace in self.cluster_charts[chart_set]:
                chart_yaml_files = []
                for chart in self.cluster_charts[chart_set][namespace]:
                    chart_yaml_files.append(self.cluster_charts[chart_set][namespace][chart]['file'])
                self.apply_charts_to_namespace(self.kubernetes_context, namespace, chart_yaml_files, 'master')

