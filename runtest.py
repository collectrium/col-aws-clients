#!/usr/bin/env python
import os
import sys

import nose

if __name__ == '__main__':
    try:
        # nose.main()
        success = nose.run(
            argv=[
                os.path.abspath(__file__),
                "--with-coverage",
                "--cover-package=col_aws_clients",
                "--cover-erase",
            ]
        )
        sys.exit(0 if success else 1)
    finally:
        pass
