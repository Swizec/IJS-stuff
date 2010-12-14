"ProviderToolbox exceptions"
import sys, traceback

class Error(Exception):

    def __str__(self):
        if len(self.args) == 1:
#            return self.__class__.__name__ + ": " + str(self.args[0])
            return str(self.args[0])
        else:
#            return self.__class__.__name__ + ": " + str(self.args)
            return str(self.args)

    def trace(self):
        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback)

class FetchError(Error):
    "Fetch module cannot fetch content"
    pass

class FeedGeneratorError(Error):
    "Feed generator related exceptions"
