#include "RBCS_OPTIONS.h"

C !INTERFACE: ==========================================================
      SUBROUTINE RBCS_GAUSSIAN_FILTER(
     U                    fieldin, fieldout, 
     I                    k, bi, bj, tracerNum,
     I                    myTime, myIter, myThid )

C !DESCRIPTION:
C     Add to tendency array the contribution from 3-D field relaxation

C !USES: ===============================================================
      IMPLICIT NONE
#include "SIZE.h"
#include "EEPARAMS.h"
#include "PARAMS.h"
#include "GRID.h"
#include "RBCS_SIZE.h"
#include "RBCS_PARAMS.h"
#include "RBCS_FIELDS.h"

C !INPUT/OUTPUT PARAMETERS: ============================================
C  gTendency      :: the tendency array
C  k              :: vertical level index
C  bi,bj          :: tile indices
C  tracerNum      :: tracer number (1=Temp, 2=Salt, >2 : ptracer)
C  myTime         :: current time
C  myIter         :: current timestep
C  myThid         :: my Thread Id number
      _RL fieldin(1-OLx:sNx+OLx,1-OLy:sNy+OLy)
      _RL fieldout(1-OLx:sNx+OLx,1-OLy:sNy+OLy)
      INTEGER k, bi, bj
      INTEGER tracerNum
      _RL myTime
      INTEGER myIter
      INTEGER myThid
C !LOCAL VARIABLES: ====================================================
      INTEGER i,j
      INTEGER kit
      _RL tmp(1-OLx:sNx+OLx,1-OLy:sNy+OLy)
      _RL tmp2(1-OLx:sNx+OLx,1-OLy:sNy+OLy)
      _RL kiter(1-OLx:sNx+OLx,1-OLy:sNy+OLy)
      _RL psi

      DO j=1,sNy
        DO i=1,sNx
          tmp(i,j) = fieldin(i,j)
C      copyt fieldout in case max_iter = -1
          fieldout(i,j) = fieldin(i,j) 
        ENDDO
      ENDDO

      _EXCH_XY_RL(tmp,myThid)

      DO kit=1,max_iter_filter
        DO j=1,sNy
          DO i=1,sNx
            tmp2(i,j) = maskC(i,j,k,bi,bj)
     $         *(tmp(i+1,j+1)*maskC(i+1,j+1,k,bi,bj)
     $         + tmp(i  ,j+1)*maskC(i  ,j+1,k,bi,bj)
     $         + tmp(i-1,j+1)*maskC(i-1,j+1,k,bi,bj)
     $         + tmp(i+1,j  )*maskC(i+1,j  ,k,bi,bj)
     $         + tmp(i  ,j  )*maskC(i  ,j  ,k,bi,bj)
     $         + tmp(i-1,j  )*maskC(i-1,j  ,k,bi,bj)
     $         + tmp(i+1,j-1)*maskC(i+1,j-1,k,bi,bj)
     $         + tmp(i  ,j-1)*maskC(i  ,j-1,k,bi,bj)
     $         + tmp(i-1,j-1)*maskC(i-1,j-1,k,bi,bj))/
     $         MAX(1.0, maskC(i+1,j+1,k,bi,bj)
     $         +        maskC(i  ,j+1,k,bi,bj)
     $         +        maskC(i-1,j+1,k,bi,bj)
     $         +        maskC(i+1,j  ,k,bi,bj)
     $         +        maskC(i  ,j  ,k,bi,bj)
     $         +        maskC(i-1,j  ,k,bi,bj)
     $         +        maskC(i+1,j-1,k,bi,bj)
     $         +        maskC(i  ,j-1,k,bi,bj)
     $         +        maskC(i-1,j-1,k,bi,bj))
          ENDDO
        ENDDO

        DO j=1,sNy
          DO i=1,sNx
            tmp(i,j) = tmp2(i,j)
            if (kit.EQ.RBC_filter_kiter(i,j,bi,bj)) THEN
              fieldout(i,j) = tmp2(i,j)
            ENDIF
          ENDDO
        ENDDO

        _EXCH_XY_RL(tmp,myThid)

      ENDDO ! kiter loop

      _EXCH_XY_RL(fieldout,myThid)      

      RETURN
      END