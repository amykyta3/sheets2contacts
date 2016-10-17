import argparse
import logging

class App:
  def __init__(self):
    
    """ Parsed command line options """
    self.options = None
    
    """ Message logger """
    self.log = logging.getLogger(type(self).__name__)
    logging.basicConfig(
      format="%(levelname)s: %(name)s - %(message)s",
      level=logging.INFO,
    )
    
  #------------------------------------------------------------------------------------------------
  def main(self):
    """
    extend or override this
    """
    self.parse_cmdline()
    
    if(self.options.verbose):
      self.log.setLevel(logging.DEBUG)
      for l in logging.Logger.manager.loggerDict.values():
        if(type(l) == logging.Logger):
          l.setLevel(logging.DEBUG)
    elif(self.options.quiet):
      self.log.setLevel(logging.WARNING)
      for l in logging.Logger.manager.loggerDict.values():
        if(type(l) == logging.Logger):
          l.setLevel(logging.WARNING)
        
  #------------------------------------------------------------------------------------------------
  def parse_cmdline(self):
    parser = argparse.ArgumentParser()
    self.set_cmdline_args(parser)
    self.options = parser.parse_args()
  
  #------------------------------------------------------------------------------------------------
  def set_cmdline_args(self, parser):
    """
    Add ArgumentParser options
    extend or override this
    """
    parser.add_argument('-q', '--quiet', dest='quiet', action='store_true',default=False,
                        help="Suppress info messages")
    parser.add_argument('--verbose', dest='verbose', action='store_true',default=False,
                        help='Enable debug messages')
  