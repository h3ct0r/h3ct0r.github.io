require 'feedjira'
require 'httparty'
require 'jekyll'

module ExternalPosts
  class ExternalPostsGenerator < Jekyll::Generator
    safe true
    priority :high

    def generate(site)
      sources = site.config['external_sources']
      return if sources.nil? || sources.empty?

      sources.each do |src|
        Jekyll.logger.info 'ExternalPosts:', "Fetching external posts from #{src['name']}"
        begin
          response = HTTParty.get(src['rss_url'], timeout: 15)
          unless response.success?
            Jekyll.logger.warn 'ExternalPosts:', "#{src['rss_url']} returned HTTP #{response.code}, skipping"
            next
          end
          feed = Feedjira.parse(response.body)
        rescue StandardError => e
          Jekyll.logger.warn 'ExternalPosts:', "Could not fetch #{src['rss_url']}: #{e.message}"
          next
        end

        feed.entries.each do |e|
          Jekyll.logger.debug 'ExternalPosts:', "...fetching #{e.url}"
          slug = e.title.downcase.strip.gsub(' ', '-').gsub(/[^\w-]/, '')
          path = site.in_source_dir("_posts/#{slug}.md")
          doc = Jekyll::Document.new(
            path, { :site => site, :collection => site.collections['posts'] }
          )
          doc.data['external_source'] = src['name']
          doc.data['feed_content'] = e.content
          doc.data['title'] = e.title.to_s
          doc.data['description'] = e.summary
          doc.data['date'] = e.published
          doc.data['redirect'] = e.url
          site.collections['posts'].docs << doc
        end
      end
    end
  end
end
