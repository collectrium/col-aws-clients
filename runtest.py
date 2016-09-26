#!/usr/bin/env python
import os

import nose

if __name__ == '__main__':
    try:
        # nose.main()
        nose.run(argv=[os.path.abspath(__file__),
                            "--with-coverage",
                       "--cover-package=col_aws_clients",
                       "--cover-erase",
                       ])
    finally:
        pass
