$(document).ready(function() {
    $('a.abstract').click(function() {
        $(this).parent().parent().find(".abstract.hidden").toggleClass('open');
    });
    $('a.bibtex').click(function() {
        $(this).parent().parent().find(".bibtex.hidden").toggleClass('open');
    });
    $('a.more-authors').on('click keydown', function(e) {
        if (e.type === 'keydown' && e.key !== 'Enter' && e.key !== ' ') return;
        e.preventDefault();
        var author = $(this).closest('.author');
        author.find('.authors-short').addClass('d-none');
        author.find('.authors-full').removeClass('d-none');
    });
    $('a').removeClass('waves-effect waves-light');
});
