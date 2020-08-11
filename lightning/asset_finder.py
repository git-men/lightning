from django.contrib.staticfiles.finders import AppDirectoriesFinder


class AssetFinder(AppDirectoriesFinder):
    def find(self, path, *args, **kwargs):
        return super().find('index.html', *args, **kwargs)
