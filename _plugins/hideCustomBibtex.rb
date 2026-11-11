module Jekyll
  module HideCustomBibtex
    def hideCustomBibtex(input)
      keywords = Array(@context.registers[:site].config['filtered_bibtex_keywords'])

      keywords.each do |keyword|
        input = input.gsub(/^.*#{Regexp.escape(keyword.to_s)}.*$\n/, '')
      end

      input
    end
  end
end

Liquid::Template.register_filter(Jekyll::HideCustomBibtex)
