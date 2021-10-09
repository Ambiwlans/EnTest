$(function () {
    var pred = parseInt($('.predlower').text() || 0);
    console.log(pred);
    
    if (pred > 0 && pred < 5000)
    {
        $('.predmain').attr("title", "Keep studying!");
    }
    if (pred > 20000 && pred < 50000)
    {
        $('.predmain').attr("title", "Native speaker?");
    }
    else ()
    {
    }

    
    //Easter egg
/*    if (pred > 1500)
    {
        $('.footer-note').html("<a href='https://github.com/Ambiwlans' target='_blank'>Ambiwlans</a>作。気に入ったら広めて下さい！");
        $('.pred-header').html("- 見積 -");
        
        $('.sharegroup').attr("title","友達を挑戦する");
        
        $('#know').html("知ってる");
        $('#dunno').html("知らない");
        $('#results').html("結果");
        $('#results').attr("title","いつでも結果の細部見える");
        
        $('.my_rank').attr("title","難しさのランキング");
        $('.count').attr("title","何番目の質問");
        $('.jlpt').attr("title","日本語能力試験");
        $('.grade').attr("title","常用漢字");
        $('.predlower').attr("title","信頼下限");
        $('.predupper').attr("title","信頼上限");
    }*/
    $('[data-toggle="tooltip"]').tooltip();
});