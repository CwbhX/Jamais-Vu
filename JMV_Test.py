from jamaisvu import Jamaisvu
import sys
import yaml


def main(config, testfile):
    filestream = open(config, "rt")
    config_information = yaml.load(filestream)
    filestream.close()

    print("Config info: %s" % config_information)
    jmv = Jamaisvu(config_information)
    jmv.fingerprint_file(testfile)


if __name__ == '__main__':
    config = sys.argv[1]
    print("Config file: %s" % config)
    testfile = sys.argv[2]
    print("Testfile: %s" % testfile)
    main(config, testfile)
