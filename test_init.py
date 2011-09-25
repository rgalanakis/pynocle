import nose
import pynocle

if __name__ == '__main__':
    m = pynocle.Monocle(outputdir='exampleoutput')
    try:
        m.makeawesome(nose.run)
    except TypeError as exc:
        #Under debugger in pycharm, it uses the wrong coverage module!
        if exc.args[0] == "__init__() got an unexpected keyword argument 'data_file'":
            m.makeawesome_nocover()
        else:
            raise