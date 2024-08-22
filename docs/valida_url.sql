CREATE DEFINER=`test`@`localhost` PROCEDURE `valida_url`(inout retCode BIGINT, inout retTxt VARCHAR(45), in url VARCHAR(500), out datos VARCHAR(5000))
/*
set @retCode = -1;
set @retTxt = '';
set @datos = "";
call valida_url(@retCode , @retTxt , 'este e s mi dato', @datos);
select @retCode , @retTxt , @datos
*/
BEGIN

set retCode = 0;
set retTxt = "Todo OK";
set datos = concat('{"valor": ', url, '}');


END