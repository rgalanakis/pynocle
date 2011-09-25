import nose
import pynocle

if __name__ == '__main__':
    m = pynocle.Monocle(outputdir='exampleoutput')
    m.makeawesome(nose.run)