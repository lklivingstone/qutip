import qutip.settings as settings
import numpy as np
import scipy
import pytest
import qutip

from qutip.core import data as _data
from qutip.core.data import Data, Dense, CSR


class TestSolve():
    def op_numpy(self, A, b):
        return np.linalg.solve(A, b)

    def _gen_op(self, N, dtype):
        return qutip.rand_unitary(N, dtype=dtype).data

    def _gen_ket(self, N, dtype):
        return qutip.rand_ket(N, dtype=dtype).data

    @pytest.mark.parametrize(['method', "opt"], [
        ("spsolve", {}),
        ("splu", {"csc": True}),
        ("gmres", {"atol": 1e-8}),
        ("lsqr", {}),
        pytest.param(
            "mkl_spsolve", {},
            marks=pytest.mark.skipif(not settings.has_mkl, reason="mkl not available")
        ),
    ],
        ids=["spsolve", "splu", "gmres", "lsqr", "mkl_spsolve"]
    )
    def test_mathematically_correct_CSR(self, method, opt):
        """
        Test that the binary operation is mathematically correct for all the
        known type specialisations.
        """
        A = self._gen_op(10, CSR)
        b = self._gen_ket(10, Dense)
        expected = self.op_numpy(A.to_array(), b.to_array())
        test = _data.solve_csr_dense(A, b, method, opt)
        test1 = _data.solve(A, b, method, opt)

        assert test.shape == expected.shape
        np.testing.assert_allclose(test.to_array(), expected,
                                   atol=1e-7, rtol=1e-7)
        np.testing.assert_allclose(test1.to_array(), expected,
                                   atol=1e-7, rtol=1e-7)

    @pytest.mark.parametrize(['method', "opt"], [
        ("solve", {}),
        ("lstsq", {}),
    ])
    def test_mathematically_correct_Dense(self, method, opt):
        A = self._gen_op(10, Dense)
        b = self._gen_ket(10, Dense)
        expected = self.op_numpy(A.to_array(), b.to_array())
        test = _data.solve_dense(A, b, method, opt)
        test1 = _data.solve(A, b, method, opt)

        assert test.shape == expected.shape
        np.testing.assert_allclose(test.to_array(), expected,
                                   atol=1e-7, rtol=1e-7)
        np.testing.assert_allclose(test1.to_array(), expected,
                                   atol=1e-7, rtol=1e-7)


    def test_incorrect_shape_non_square(self):
        A = qutip.Qobj(np.random.rand(5, 10)).data
        b = qutip.Qobj(np.random.rand(10, 1)).data
        with pytest.raises(ValueError):
            test1 = _data.solve(A, b)


    def test_incorrect_shape_mismatch(self):
        A = qutip.Qobj(np.random.rand(10, 10)).data
        b = qutip.Qobj(np.random.rand(9, 1)).data
        with pytest.raises(ValueError):
            test1 = _data.solve(A, b)


class TestSVD():
    def op_numpy(self, A):
        return np.linalg.svd(A)

    def _gen_dm(self, N, rank, dtype):
        return qutip.rand_dm(N, rank=rank, dtype=dtype).data

    def _gen_non_square(self, N):
        mat = np.random.randn(N, N//2)
        for i in range(N//2):
            # Ensure no zeros singular values
            mat[i,i] += 5
        return _data.Dense(mat)

    @pytest.mark.parametrize("shape", ["square", "non-square"])
    def test_mathematically_correct_svd(self, shape):
        if shape == "square":
            matrix = self._gen_dm(10, 6, Dense)
        else:
            matrix = self._gen_non_square(12)
        u, s, v = self.op_numpy(matrix.to_array())
        test_U, test_S, test_V = _data.svd(matrix, True)
        only_S = _data.svd(matrix, False)

        assert sum(test_S > 1e-10) == 6
        # columns are definied up to a sign
        np.testing.assert_allclose(
            np.abs(test_U.to_array()), np.abs(u), atol=1e-7, rtol=1e-7
        )
        # rows are definied up to a sign
        np.testing.assert_allclose(
            np.abs(test_V.to_array()), np.abs(v), atol=1e-7, rtol=1e-7
        )
        np.testing.assert_allclose(test_S, s, atol=1e-7, rtol=1e-7)
        np.testing.assert_allclose(only_S, s, atol=1e-7, rtol=1e-7)

        s_as_matrix = _data.diag(test_S, 0, (test_U.shape[1], test_V.shape[0]))

        np.testing.assert_allclose(
            matrix.to_array(),
            (test_U @ s_as_matrix @ test_V).to_array(),
            atol=1e-7, rtol=1e-7
        )

    def test_mathematically_correct_svd_csr(self):
        rank = 5
        matrix = self._gen_dm(100, rank, CSR)
        test_U, test_S1, test_V = _data.svd_csr(matrix, True, k=rank)
        test_S2 = _data.svd_csr(matrix, False, k=rank)

        assert len(test_S1) == rank
        assert len(test_S2) == rank

        np.testing.assert_allclose(
            matrix.to_array(),
            (test_U @ _data.diag(test_S1, 0) @ test_V).to_array(),
            atol=1e-7, rtol=1e-7
        )
