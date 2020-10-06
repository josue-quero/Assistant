
"""
Certificate Parser, a librery to facilitate the consult of 
final certificates of mexican High School available
to the general public

Copyright (C) 2020
David Josué Marcial Quero
"""

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.

import logging
import requests
import concurrent.futures
from robobrowser import RoboBrowser


class CertificateParser:
    _retry_attempts = 4
    _batch_size = 1000
    _base_url = "http://www.pace.sep.gob.mx/"
    _base_url += "certificadosdgb/certificadoremesadetalles/"
    _base_field = "#_s_com_dgb_sep_domain_CertificadoRemesaDetalle_"
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.NullHandler())

    @classmethod
    def batchSize(cls):
        return cls._batch_size

    def _getField(self, field_name):
        return f"{self._base_field}{field_name}_{field_name}_id"

    def parse(self, number_code):
        browser = RoboBrowser(parser="lxml", history=False)

        request_ok = False
        attempts = 0

        while not request_ok and attempts < self._retry_attempts:
            try:
                browser.open(f"{self._base_url}{number_code}", timeout=10)
                request_ok = True

            except requests.exceptions.ConnectionError:
                self.logger.warning(f"Failed to retrieve page {number_code}")
                attempts += 1
            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout on page {number_code}")
                attempts += 1

        if not request_ok:
            self.logger.exception(f"Connection error on {number_code}")
            return False

        self.logger.debug(f"Opened URL {self._base_url}{number_code}")

        plantel = browser.select(self._getField("tmpNombrePlantel"))

        if plantel:
            self.logger.debug(f"Certificate found on code {number_code}")

            clave = browser.select(self._getField("tmpClaveCct"))
            rvoe = browser.select(self._getField("tmpRvoe"))
            tipo = browser.select(self._getField("tmpTipoCertificado"))
            cert = browser.select(self._getField("tmpFolioDigital"))
            nombre = browser.select(self._getField("tmpNombreCompleto"))
            matricula = browser.select(self._getField("matricula"))
            promedio = browser.select(self._getField("promedio"))
            periodo = browser.select(self._getField("tmpPeriodo"))
            # curp = browser.select(self._getField("idAlumno"))

            try:
                student_dict = {"number": number_code,
                                "nombre": nombre[0].string,
                                "plantel": plantel[0].string,
                                "clave_trabajo": clave[0].string,
                                "rvoe": rvoe[0].string,
                                "matricula": matricula[0].string,
                                "promedio": promedio[0].string,
                                "periodo": periodo[0].string,
                                "tipo_certificado": tipo[0].string,
                                "certificado": cert[0].string}

            # CURP is no longer shown as part of certificate data
            # Change estimated Late 2019 - Early 2020
            # "curp": curp[0].string,

            except IndexError:
                self.logger.exception(f"Fields missing on {number_code}")
                return False

            self.logger.info(f"Parsed {student_dict['certificado']}")
            return student_dict

        else:
            self.logger.warning(f"No certificate under code {number_code}")
            return None

    def retrieveBatch(self, file_no, threaded):
        cert_list = []
        range_start = self._batch_size * file_no
        cert_range = range(range_start, range_start + self._batch_size)

        self.logger.info(f"Starting batch number {file_no}")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            map_mode = map

            if threaded:
                map_mode = executor.map

            cert_list = map_mode(self.parse, cert_range)

        if not threaded:
            cert_list = list(cert_list)

        # Finalise operation
        self.logger.info(f"Completed batch number {file_no}")
        failed_certs = cert_list.count(False)

        if failed_certs >= 1:
            self.logger.warning(f"{failed_certs} elements could not be obtained")
            failure_rate = (failed_certs / self._batch_size) * 100

            self.logger.warning(f"{failure_rate}% failure rate")

        return cert_list


def main():
    print("Certificate Parser, a librery to facilitate consulting")
    print("of high school mexican certificates")
    print()
    print("To use this librery, import it from another script")
    print("Or from the console")
    print()
    print("Copyright (C) 2020")
    print("David Josué Marcia Quero")


if __name__ == '__main__':
    main()
